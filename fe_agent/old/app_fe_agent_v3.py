# ============================================================
#  app_fe_agent_v3.py
#  Versión 3 - Agente FE integrado con Action Router y n8n
# ============================================================
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-28
# ============================================================

import streamlit as st
import json
from datetime import datetime

# ------------------------------------------------------------
#  Importación de módulos del núcleo
# ------------------------------------------------------------
from core.ambiguity_manager import AmbiguityManager
from core.llm_interpreter_conceptos_v2 import LLMInterpreter
from core.language_generator import LanguageGenerator
from core.n8n_connector_v2 import N8NConnector
from core.context_manager import ContextManager

# ------------------------------------------------------------
#  Configuración inicial
# ------------------------------------------------------------
st.set_page_config(page_title="Agente FE", layout="wide")
st.title("🤖 Agente FE - Ferretería Inteligente (v3)")

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.chat_history = []
    st.session_state.ambiguity_manager = AmbiguityManager()
    st.session_state.llm_interpreter = LLMInterpreter()
    st.session_state.language_generator = LanguageGenerator()
    st.session_state.n8n_connector = N8NConnector("data/FE_action_router.json")
    st.session_state.context_manager = ContextManager()
    st.toast("Agente FE inicializado correctamente ✅")

# ------------------------------------------------------------
#  Interfaz conversacional
# ------------------------------------------------------------
st.markdown("---")
st.markdown("### 💬 Interactúa con el Agente FE")

user_input = st.chat_input("Escribe una consulta (por ejemplo: '¿Cuál fue el margen global del último trimestre?')")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # 1️⃣ Evaluación de ambigüedad
    am = st.session_state.ambiguity_manager
    result = am.procesar_input(user_input)

    if result["requiere_clarificacion"]:
        st.chat_message("assistant").write(result["mensaje"])

    else:
        # 2️⃣ Interpretación semántica
        llm = st.session_state.llm_interpreter
        parsed = llm.interpret(result["mensaje"])

        st.chat_message("assistant").write("🧠 Interpretando tu solicitud...")
        st.json(parsed)

        # 3️⃣ Ejecución con n8n
        accion = parsed.get("accion")
        parametros = parsed.get("parametros", {})
        st.chat_message("assistant").write(f"⚙️ Ejecutando acción: **{accion}**")

        response = st.session_state.n8n_connector.execute(accion, parametros)

        if response.get("ok"):
            data = response.get("data", {})
            resumen = st.session_state.language_generator.generate(accion, data)
            st.chat_message("assistant").write(resumen)

            # Visualización de resultados
            if isinstance(data, dict) and "tabla" in data:
                st.dataframe(data["tabla"])
            elif isinstance(data, list):
                st.dataframe(data)
            else:
                st.write(data)

            # Guardar en contexto
            st.session_state.context_manager.update(user_input, resumen, metadata=response)

        else:
            st.error(f"❌ Error: {response.get('error')}")
            st.session_state.context_manager.update(user_input, f"Error: {response.get('error')}", metadata=response)

# ------------------------------------------------------------
#  Panel lateral de control
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Opciones del Agente")
    if st.button("🧹 Limpiar conversación"):
        st.session_state.chat_history = []
        st.session_state.context_manager.clear()
        st.success("Conversación reiniciada.")

    st.markdown("### 📜 Historial reciente")
    for msg in st.session_state.chat_history[-10:]:
        st.write(f"**{msg['role']}**: {msg['content']}")

    st.markdown("---")
    st.caption(f"Versión: v3 | Última actualización: {datetime.now().strftime('%d-%m-%Y')}")
