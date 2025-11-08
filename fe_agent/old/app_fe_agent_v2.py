# ============================================================
#  app_fe_agent_v2.py
#  Versión 2 - Agente FE (Ferretería Inteligente)
# ============================================================
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-28
# ------------------------------------------------------------
#  Descripción:
#  Versión completamente integrada del agente FE.
#  Incorpora AmbiguityManager, LLMInterpreter, N8nConnector,
#  ContextManager y LanguageGenerator dentro del flujo Streamlit.
# ============================================================

import streamlit as st
import json
import requests
from datetime import datetime

# ------------------------------------------------------------
#  Importación de módulos del núcleo
# ------------------------------------------------------------
from core.ambiguity_manager import AmbiguityManager
from core.llm_interpreter_conceptos_v2 import LLMInterpreter
# Los siguientes módulos se integrarán en iteraciones posteriores
# (pueden ser plantillas vacías por ahora)
# ------------------------------------------------------------
# from core.context_manager import ContextManager
# from core.language_generator import LanguageGenerator
# from core.n8n_connector import N8nConnector
# ------------------------------------------------------------

# ------------------------------------------------------------
#  Configuración inicial
# ------------------------------------------------------------
st.set_page_config(page_title="Agente FE", layout="wide")
st.title("🤖 Agente FE - Ferretería Inteligente (v2)")

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.chat_history = []
    st.session_state.ambiguity_manager = AmbiguityManager()
    st.session_state.llm_interpreter = LLMInterpreter()
    st.session_state.context = {}
    st.session_state.pending_clarification = False
    # st.session_state.language_generator = LanguageGenerator()
    # st.session_state.n8n_connector = N8nConnector()
    st.toast("Agente inicializado correctamente.")

# ------------------------------------------------------------
#  Interfaz de conversación (modo chat)
# ------------------------------------------------------------
st.markdown("---")
st.markdown("### 💬 Interactúa con el Agente FE")

user_input = st.chat_input("Escribe una consulta (por ejemplo: '¿Cuál fue el margen global del último trimestre?')")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # --------------------------------------------------------
    # 1️⃣ Evaluación de ambigüedad
    # --------------------------------------------------------
    am = st.session_state.ambiguity_manager
    result = am.procesar_input(user_input)

    if result["requiere_clarificacion"]:
        st.session_state.pending_clarification = True
        st.chat_message("assistant").write(result["mensaje"])
    else:
        st.session_state.pending_clarification = False

        # ----------------------------------------------------
        # 2️⃣ Interpretación semántica con LLM
        # ----------------------------------------------------
        llm = st.session_state.llm_interpreter
        parsed = llm.interpret(result["mensaje"])

        st.chat_message("assistant").write("🧠 Interpretando tu solicitud...")
        st.json(parsed)

        # ----------------------------------------------------
        # 3️⃣ Ejecución (placeholder de n8n)
        # ----------------------------------------------------
        # Aquí se conectará N8nConnector (versión futura)
        # Simulación temporal:
        simulated_result = {
            "tabla": [{"producto": "Taladro 500W", "ventas": 12500, "margen": "32%"}],
            "resumen": "El producto con mayor ingreso fue el Taladro 500W, con ventas de $12.500 y un margen del 32%."
        }

        # ----------------------------------------------------
        # 4️⃣ Generación de respuesta natural
        # ----------------------------------------------------
        # Cuando se integre language_generator, reemplazar esta sección:
        final_response = simulated_result["resumen"]
        st.chat_message("assistant").write(final_response)

        # ----------------------------------------------------
        # 5️⃣ Visualización de resultados
        # ----------------------------------------------------
        st.dataframe(simulated_result["tabla"])
        st.session_state.chat_history.append({"role": "assistant", "content": final_response})

# ------------------------------------------------------------
#  Historial y depuración
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Opciones del Agente")
    if st.button("🧹 Limpiar conversación"):
        st.session_state.chat_history = []
        st.session_state.pending_clarification = False
        st.success("Conversación reiniciada.")

    st.markdown("### 📜 Historial")
    for msg in st.session_state.chat_history[-10:]:
        st.write(f"**{msg['role']}**: {msg['content']}")

    st.markdown("---")
    st.caption(f"Versión: v2 | Última actualización: {datetime.now().strftime('%d-%m-%Y')}")

