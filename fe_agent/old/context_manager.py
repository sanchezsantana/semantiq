# ============================================================
#  core/context_manager.py
#  Versión 1 - Gestión de memoria de sesión
# ============================================================

import streamlit as st
from datetime import datetime

class ContextManager:
    """
    Maneja el contexto de conversación del usuario dentro de Streamlit.
    Guarda el historial de preguntas, respuestas y metadatos de sesión.
    """

    def __init__(self):
        if "context" not in st.session_state:
            st.session_state.context = {
                "historial": [],
                "ultima_pregunta": None,
                "ultima_respuesta": None,
                "timestamp_inicio": datetime.now().isoformat()
            }

    def update(self, pregunta: str, respuesta: str, metadata: dict = None):
        """Registra una nueva interacción"""
        entry = {
            "pregunta": pregunta,
            "respuesta": respuesta,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.context["historial"].append(entry)
        st.session_state.context["ultima_pregunta"] = pregunta
        st.session_state.context["ultima_respuesta"] = respuesta

    def get_last(self):
        """Devuelve la última interacción"""
        return {
            "pregunta": st.session_state.context.get("ultima_pregunta"),
            "respuesta": st.session_state.context.get("ultima_respuesta")
        }

    def clear(self):
        """Reinicia el contexto de conversación"""
        st.session_state.context = {
            "historial": [],
            "ultima_pregunta": None,
            "ultima_respuesta": None,
            "timestamp_inicio": datetime.now().isoformat()
        }
