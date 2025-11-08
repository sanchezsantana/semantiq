# ============================================================
#  core/context_manager_v3.py
#  Versión 3 - Contexto cognitivo persistente + FT simulado
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-29
# ============================================================

from __future__ import annotations
import streamlit as st
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

DEFAULT_SESSION_PATH = "data/session_log.json"
CONTEXT_KEY = "context"

class ContextManager:
    """
    Maneja el contexto cognitivo del agente FE dentro de Streamlit.
    - Memoria de sesión (historial breve y campos "últimos")
    - Preferencias del usuario (p.ej., visualización)
    - Estado conversacional (gráfico pendiente, aclaraciones)
    - Persistencia local (save/load)
    - Exposición de un snapshot compacto para el FT simulado (to_llm_context)
    """

    def __init__(self,
                 persist_path: str = DEFAULT_SESSION_PATH,
                 max_historial: int = 30):
        self.persist_path = persist_path
        self.max_historial = max_historial

        if CONTEXT_KEY not in st.session_state:
            st.session_state[CONTEXT_KEY] = self._crear_contexto_base()
        # Cargar si existe persistencia previa
        self.load_from_file(self.persist_path)

        # Compatibilidad hacia atrás: asegurar claves v3
        self._ensure_keys()

    # ------------------------------------------------------------
    #  ESTRUCTURA BASE
    # ------------------------------------------------------------
    def _crear_contexto_base(self) -> Dict[str, Any]:
        now = datetime.now().isoformat()
        return {
            "version": "v3",
            "timestamp_inicio": now,
            "timestamp_ultima_actualizacion": now,
            # Conversación
            "historial": [],                 # Lista de {pregunta, respuesta, metadata, timestamp}
            "ultima_pregunta": None,
            "ultima_respuesta": None,
            "ultima_accion": None,           # Acción ejecutada más reciente (para LLM FT-sim)
            # Visualización / tablas
            "ultima_tabla": None,            # Última tabla (lista de dicts) para graficar
            "grafico_pendiente": False,      # ¿Hay una pregunta abierta para mostrar gráfico?
            "solicita_grafico": False,       # ¿El usuario pidió explícitamente gráfico?
            "preferencia_visual": "auto",    # "auto" | "siempre" | "nunca"
            # Ambigüedad / aclaración
            "clarificacion_pendiente": None, # Texto de la aclaración pendiente, si aplica
            # Usuario
            "usuario_id": "anonimo"
        }

    def _ensure_keys(self) -> None:
        """Garantiza que existan campos nuevos en sesiones antiguas."""
        ctx = st.session_state[CONTEXT_KEY]
        defaults = self._crear_contexto_base()
        for k, v in defaults.items():
            if k not in ctx:
                ctx[k] = v

    # ------------------------------------------------------------
    #  GETTERS / SETTERS SENCILLOS
    # ------------------------------------------------------------
    @property
    def context(self) -> Dict[str, Any]:
        return st.session_state[CONTEXT_KEY]

    def get(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)

    def update(self, key: Optional[str] = None, value: Any = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Dos modos:
        - update(key, value): actualiza un campo simple del contexto.
        - update(metadata={ 'pregunta':..., 'respuesta':..., 'metadata':{...} }): registra una interacción completa.
        """
        ts = datetime.now().isoformat()

        # Actualización directa de clave/valor
        if key is not None:
            self.context[key] = value
            self.context["timestamp_ultima_actualizacion"] = ts
            return

        # Registro de interacción en historial
        if metadata and "pregunta" in metadata and "respuesta" in metadata:
            entry = {
                "pregunta": metadata["pregunta"],
                "respuesta": metadata["respuesta"],
                "metadata": metadata.get("metadata", {}),
                "timestamp": ts
            }
            self.context["historial"].append(entry)
            # Rotar historial si excede
            if len(self.context["historial"]) > self.max_historial:
                self.context["historial"] = self.context["historial"][-self.max_historial:]

            self.context["ultima_pregunta"] = metadata["pregunta"]
            self.context["ultima_respuesta"] = metadata["respuesta"]
            self.context["timestamp_ultima_actualizacion"] = ts

    def update_last_action(self, accion: Optional[str]) -> None:
        """Guarda la última acción ejecutada (para FT-sim y trazabilidad)."""
        self.update("ultima_accion", accion)

    def set_user_id(self, user_id: str) -> None:
        self.update("usuario_id", user_id)

    # ------------------------------------------------------------
    #  VISUALIZACIÓN: flujo conversacional de gráficos
    # ------------------------------------------------------------
    def mark_graph_pending(self, ultima_tabla: Optional[List[Dict[str, Any]]]) -> None:
        """Marca que hay un gráfico pendiente de confirmación y guarda la última tabla."""
        self.update("ultima_tabla", ultima_tabla or [])
        self.update("grafico_pendiente", True)

    def clear_graph_pending(self) -> None:
        self.update("grafico_pendiente", False)

    def set_visual_preference(self, preference: str) -> None:
        """
        Define preferencia persistente del usuario para gráficos.
        Valores soportados: "auto" | "siempre" | "nunca"
        """
        if preference not in ("auto", "siempre", "nunca"):
            preference = "auto"
        self.update("preferencia_visual", preference)

    def resolve_graph_answer(self, user_text: str) -> Optional[bool]:
        """
        Interpreta respuestas breves del usuario para la pregunta:
        '¿Deseas gráfico?'  -> True/False/None
        """
        if not isinstance(user_text, str):
            return None
        t = user_text.strip().lower()
        positivos = {"si", "sí", "claro", "por favor", "ok", "dale"}
        negativos = {"no", "no gracias", "gracias, no"}
        if t in positivos:
            return True
        if t in negativos:
            return False
        return None

    def set_preference_from_answer(self, user_text: str) -> None:
        """
        Heurística opcional: si el usuario insiste varias veces en 'sí' o 'no',
        podríamos fijar preferencia en 'siempre' o 'nunca'. Por simplicidad:
        - Si responde 'sí' 2 veces consecutivas, set 'siempre'
        - Si responde 'no'  2 veces consecutivas, set 'nunca'
        """
        # Esta función puede enriquecerse con contadores; mantendremos simple.
        pass

    # ------------------------------------------------------------
    #  CONTEXTO PARA LLM (FT simulado)
    # ------------------------------------------------------------
    def to_llm_context(self, limit_historial: int = 5) -> Dict[str, Any]:
        """
        Devuelve un snapshot compacto para pasar al LLMInterpreterV3.
        Incluye los últimos turnos (sin datos sensibles) y banderas útiles.
        """
        h = self.context.get("historial", [])
        ultimos = h[-limit_historial:] if h else []
        return {
            "ultima_accion": self.context.get("ultima_accion"),
            "ultima_respuesta": self.context.get("ultima_respuesta"),
            "preferencia_visual": self.context.get("preferencia_visual", "auto"),
            "usuario_id": self.context.get("usuario_id", "anonimo"),
            "historial_reciente": [
                {
                    "pregunta": i.get("pregunta"),
                    "respuesta": i.get("respuesta"),
                    "timestamp": i.get("timestamp"),
                } for i in ultimos
            ],
            "grafico_pendiente": self.context.get("grafico_pendiente", False),
        }

    def get_last(self) -> Dict[str, Any]:
        """Devuelve la última interacción básica."""
        return {
            "pregunta": self.context.get("ultima_pregunta"),
            "respuesta": self.context.get("ultima_respuesta"),
            "timestamp": self.context.get("timestamp_ultima_actualizacion"),
            "accion": self.context.get("ultima_accion")
        }

    # ------------------------------------------------------------
    #  PERSISTENCIA LOCAL
    # ------------------------------------------------------------
    def save_to_file(self, filepath: Optional[str] = None) -> None:
        """Guarda el contexto completo en un archivo JSON."""
        path = filepath or self.persist_path
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            snapshot = {
                "timestamp_guardado": datetime.now().isoformat(),
                "context": self.context
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # Evita romper la app por persistencia
            print(f"[ContextManager v3] Error al guardar contexto: {e}")

    def load_from_file(self, filepath: Optional[str] = None) -> None:
        """Carga el contexto desde un archivo JSON si existe; caso contrario, crea base."""
        path = filepath or self.persist_path
        if not os.path.exists(path):
            # Sin archivo aún: mantener base
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                snapshot = json.load(f)
            loaded = snapshot.get("context")
            if isinstance(loaded, dict):
                # Merge suave para mantener compatibilidad y nuevos campos
                base = self._crear_contexto_base()
                base.update(loaded)
                st.session_state[CONTEXT_KEY] = base
            else:
                st.session_state[CONTEXT_KEY] = self._crear_contexto_base()
        except Exception as e:
            print(f"[ContextManager v3] Error al cargar contexto: {e}")
            st.session_state[CONTEXT_KEY] = self._crear_contexto_base()

    # ------------------------------------------------------------
    #  LIMPIEZA Y REINICIO
    # ------------------------------------------------------------
    def clear(self) -> None:
        """Reinicia completamente el contexto y borra historial."""
        st.session_state[CONTEXT_KEY] = self._crear_contexto_base()

