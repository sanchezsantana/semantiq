# ============================================================
#  core/context_manager.py
#  Versión 2 - Contexto cognitivo persistente
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-29
# ============================================================

import streamlit as st
import json
import os
from datetime import datetime

class ContextManager:
    """
    Maneja el contexto cognitivo del agente FE dentro de Streamlit.
    Guarda historial, últimas interacciones y estados persistentes:
    - grafico_pendiente: si el usuario debe confirmar visualización
    - solicita_grafico: si el usuario pidió explícitamente un gráfico
    - ultima_tabla: última tabla presentada para graficar
    - clarificacion_pendiente: pregunta ambigua que requiere detalle
    """

    def __init__(self):
        if "context" not in st.session_state:
            st.session_state.context = self._crear_contexto_base()

    # ------------------------------------------------------------
    #  ESTRUCTURA BASE
    # ------------------------------------------------------------
    def _crear_contexto_base(self):
        """Devuelve la estructura base de contexto."""
        return {
            "historial": [],
            "ultima_pregunta": None,
            "ultima_respuesta": None,
            "ultima_tabla": None,
            "grafico_pendiente": False,
            "solicita_grafico": False,
            "clarificacion_pendiente": None,
            "timestamp_inicio": datetime.now().isoformat()
        }

    # ------------------------------------------------------------
    #  ACTUALIZACIÓN GENERAL
    # ------------------------------------------------------------
    def update(self, key: str = None, value=None, metadata: dict = None):
        """
        Actualiza una parte del contexto o registra una interacción completa.
        Si se pasan key y value, actualiza directamente el contexto.
        Si se pasan pregunta y respuesta, crea una entrada en historial.
        """
        ctx = st.session_state.context
        timestamp = datetime.now().isoformat()

        # Actualización directa de clave/valor
        if key:
            ctx[key] = value
            ctx["timestamp_ultima_actualizacion"] = timestamp
            return

        # Caso general: actualización de pregunta/respuesta
        if metadata and "pregunta" in metadata and "respuesta" in metadata:
            entry = {
                "pregunta": metadata["pregunta"],
                "respuesta": metadata["respuesta"],
                "metadata": metadata.get("metadata", {}),
                "timestamp": timestamp
            }
            ctx["historial"].append(entry)
            ctx["ultima_pregunta"] = metadata["pregunta"]
            ctx["ultima_respuesta"] = metadata["respuesta"]
            ctx["timestamp_ultima_actualizacion"] = timestamp

    # ------------------------------------------------------------
    #  OBTENCIÓN DE INFORMACIÓN
    # ------------------------------------------------------------
    def get(self, key: str):
        """Obtiene el valor de una clave específica del contexto."""
        return st.session_state.context.get(key)

    def get_last(self):
        """Devuelve la última interacción completa."""
        return {
            "pregunta": st.session_state.context.get("ultima_pregunta"),
            "respuesta": st.session_state.context.get("ultima_respuesta"),
            "timestamp": st.session_state.context.get("timestamp_ultima_actualizacion")
        }

    # ------------------------------------------------------------
    #  PERSISTENCIA LOCAL
    # ------------------------------------------------------------
    def save_to_file(self, filepath="data/session_log.json"):
        """Guarda el contexto completo en un archivo JSON."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        snapshot = {
            "timestamp_guardado": datetime.now().isoformat(),
            "context": st.session_state.context
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath="data/session_log.json"):
        """Carga el contexto desde un archivo JSON si existe."""
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    snapshot = json.load(f)
                st.session_state.context = snapshot.get("context", self._crear_contexto_base())
            except Exception as e:
                print(f"[ContextManager] Error al cargar contexto: {e}")
                st.session_state.context = self._crear_contexto_base()
        else:
            st.session_state.context = self._crear_contexto_base()

    # ------------------------------------------------------------
    #  LIMPIEZA Y REINICIO
    # ------------------------------------------------------------
    def clear(self):
        """Reinicia completamente el contexto."""
        st.session_state.context = self._crear_contexto_base()
