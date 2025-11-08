"""
fallback_manager.py
---------------------------------
Módulo: FallbackManager
Autor: Eduardo Sánchez Santana
Versión: 1.0 (extendida)

Función:
Gestiona los escenarios de error o incertidumbre cognitiva del Agente FE.
Proporciona respuestas empáticas al usuario y registra trazabilidad completa
del fallo, incluyendo acción, parámetros y tipo de error.

Casos gestionados:
  1️⃣ Falta de reconocimiento del LLM (sin acción)
  2️⃣ Falla técnica o de red en n8n
  3️⃣ Ambigüedad semántica no resuelta
  4️⃣ Error general no previsto
---------------------------------
"""

import json
import datetime
import os
from typing import Dict, Any, Optional


class FallbackManager:
    def __init__(self, log_file: str = "data/fallback_log.jsonl"):
        """
        Inicializa el gestor de fallback y crea el archivo de log si no existe.
        Cada evento se registra como una línea JSON independiente.
        """
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # ---------------------------------------------------
    # 🧩 MÉTODO PRINCIPAL
    # ---------------------------------------------------

    def handle(
        self,
        user_input: str,
        motivo: str,
        tipo: Optional[str] = None,
        accion: Optional[str] = None,
        parametros: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Gestiona un evento de fallback y devuelve un diccionario con:
        - texto legible para Streamlit
        - metadatos para diagnóstico
        """
        tipo = tipo or self._inferir_tipo(motivo)
        texto = self._crear_mensaje(tipo, motivo)

        evento = {
            "timestamp": datetime.datetime.now().isoformat(),
            "tipo": tipo,
            "motivo": motivo,
            "entrada_usuario": user_input,
            "accion": accion or "no_definida",
            "parametros": parametros or {},
            "respuesta_generada": texto,
        }

        self._registrar_evento(evento)
        return {
            "texto": texto,
            "motivo": motivo,
            "tipo": tipo,
            "accion": accion,
            "timestamp": evento["timestamp"],
        }

    # ---------------------------------------------------
    # 🧠 DETECCIÓN AUTOMÁTICA DE TIPO
    # ---------------------------------------------------

    def _inferir_tipo(self, motivo: str) -> str:
        """Intenta clasificar el tipo de error según el texto del motivo."""
        motivo_l = motivo.lower()
        if "n8n" in motivo_l or "webhook" in motivo_l or "conexion" in motivo_l:
            return "n8n"
        elif "acción" in motivo_l or "accion" in motivo_l or "llm" in motivo_l:
            return "llm"
        elif "ambigu" in motivo_l:
            return "ambiguous"
        else:
            return "general"

    # ---------------------------------------------------
    # 💬 PLANTILLAS DE RESPUESTA
    # ---------------------------------------------------

    def _crear_mensaje(self, tipo: str, motivo: str) -> str:
        """Genera un mensaje coherente según el tipo de fallo."""
        mensajes = {
            "llm": (
                "🤔 No logré interpretar con claridad tu solicitud. "
                "Podrías reformularla o especificar mejor qué período, producto o métrica deseas consultar."
            ),
            "n8n": (
                f"⚙️ Ocurrió un problema al ejecutar el flujo operativo. "
                f"Motivo: *{motivo}*. "
                "Por favor intenta nuevamente o revisa la disponibilidad del flujo en n8n."
            ),
            "ambiguous": (
                "❓ Tu consulta parece tener más de un significado posible. "
                "¿Podrías aclarar exactamente a qué te refieres?"
            ),
            "general": (
                f"⚠️ No pude completar tu solicitud ({motivo}). "
                "Por favor intenta de nuevo o formula la pregunta de otra manera."
            ),
        }
        return mensajes.get(tipo, mensajes["general"])

    # ---------------------------------------------------
    # 🪵 REGISTRO DE EVENTOS
    # ---------------------------------------------------

    def _registrar_evento(self, evento: Dict[str, Any]) -> None:
        """Guarda el evento de fallback en formato JSONL."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(evento, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[FallbackManager] Error al registrar log: {e}")

    # ---------------------------------------------------
    # 📜 UTILIDADES
    # ---------------------------------------------------

    def leer_log(self, max_registros: int = 10) -> list:
        """Devuelve los últimos registros de fallback."""
        if not os.path.exists(self.log_file):
            return []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lineas = f.readlines()[-max_registros:]
                return [json.loads(l) for l in lineas]
        except Exception as e:
            print(f"[FallbackManager] Error al leer log: {e}")
            return []

    def limpiar_log(self) -> None:
        """Vacía el archivo de log."""
        try:
            open(self.log_file, "w", encoding="utf-8").close()
        except Exception as e:
            print(f"[FallbackManager] Error al limpiar log: {e}")
