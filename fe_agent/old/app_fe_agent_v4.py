# ============================================================
#  app_fe_agent_v4.py
#  Versión 4 (consolidada)
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
from core.fallback_manager import FallbackManager

# ------------------------------------------------------------
#  CONFIGURACIÓN DE PÁGINA E INICIALIZACIÓN
# ------------------------------------------------------------
st.set_page_config(page_title="Agente FE - Ferretería Inteligente", layout="wide")

st.title("🤖 Agente FE - Ferretería Inteligente (v4)")
st.caption("Versión consolidada con fallback, logging, historial y modo debug")

# ------------------------------------------------------------
#  INICIALIZACIÓN DE SESIÓN
# ------------------------------------------------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.chat_history = []
    st.session_state.ambiguity_manager = AmbiguityManager()
    st.session_state.llm_interpreter = LLMInterpreter()
    st.session_state.language_generator = LanguageGenerator()
    st.session_state.n8n_connector = N8NConnector("data/FE_action_router.json")
    st.session_state.context_manager = ContextManager()
    st.session_state.fallback_manager = FallbackManager()
    st.toast("Agente FE inicializado correctamente ✅")

# ------------------------------------------------------------
#  PANEL LATERAL DE CONTROL (v4 consolidado)
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Opciones del Agente")

    if st.button("🧹 Limpiar conversación y contexto"):
        st.session_state.chat_history = []
        st.session_state.context_manager.clear()
        st.session_state.fallback_manager.limpiar_log()
        st.success("Conversación, contexto y logs reiniciados.")

    debug_mode = st.checkbox("🩺 Activar modo debug", value=False)

    st.markdown("### 📜 Historial reciente")
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history[-10:]:
            if msg["role"] == "user":
                st.write(f"🧍‍♂️ **Tú:** {msg['content']}")
            else:
                st.write(f"🤖 **Agente:** {msg['content']}")
    else:
        st.caption("No hay mensajes recientes.")

    st.markdown("### 🪵 Fallbacks recientes")
    logs = st.session_state.fallback_manager.leer_log(5)
    if logs:
        for item in logs:
            tipo = item.get("tipo", "general")
            icono = "⚙️" if tipo == "n8n" else "🤔" if tipo == "llm" else "⚠️"
            st.caption(f"{icono} {item['timestamp']} — {tipo.upper()}: {item['motivo']}")
    else:
        st.caption("Sin registros recientes de fallback.")

    st.markdown("---")
    st.caption(f"Versión: v4 | Última actualización: {datetime.now().strftime('%d-%m-%Y %H:%M')}")

# ------------------------------------------------------------
#  INTERFAZ PRINCIPAL TIPO CHAT
# ------------------------------------------------------------
st.markdown("---")
st.markdown("### 💬 Interactúa con el agente")

user_input = st.chat_input("Ejemplo: '¿Cuáles fueron los productos más vendidos este mes?'")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # 1️⃣ DETECCIÓN DE AMBIGÜEDAD
    am = st.session_state.ambiguity_manager
    ambiguity_result = am.procesar_input(user_input)

    if ambiguity_result["requiere_clarificacion"]:
        st.chat_message("assistant").warning(ambiguity_result["mensaje"])
        st.session_state.context_manager.update(
            key="ultima_respuesta",
            value=ambiguity_result["mensaje"]
        )
        st.stop()

    # 2️⃣ INTERPRETACIÓN CON LLM
    st.chat_message("assistant").info("🧠 Analizando tu consulta...")
    llm = st.session_state.llm_interpreter
    parsed = llm.interpret(ambiguity_result["mensaje"])

    if debug_mode:
        with st.expander("🧩 JSON interpretado por LLM"):
            st.json(parsed)

    accion = parsed.get("accion")
    parametros = parsed.get("parametros", {})

    # 🧩 Fallback: sin acción reconocida
    if not accion:
        fb = st.session_state.fallback_manager
        respuesta = fb.handle(
            user_input,
            "Sin acción detectada por el LLM",
            tipo="llm"
        )
        st.chat_message("assistant").warning(respuesta["texto"])
        st.session_state.context_manager.update(
            key="ultima_respuesta",
            value=respuesta["texto"],
        )
        st.stop()

    # 3️⃣ EJECUCIÓN EN n8n
    st.chat_message("assistant").write(f"⚙️ Ejecutando acción: **{accion}**")

    try:
        response = st.session_state.n8n_connector.execute(accion, parametros)
    except Exception as e:
        fb = st.session_state.fallback_manager
        respuesta = fb.handle(
            user_input,
            str(e),
            tipo="n8n",
            accion=accion,
            parametros=parametros
        )
        st.chat_message("assistant").error(respuesta["texto"])
        st.session_state.context_manager.update(
            key="ultima_respuesta",
            value=respuesta["texto"],
            metadata=respuesta
        )
        st.stop()

    # 4️⃣ PROCESAMIENTO DE RESULTADOS
    if response.get("ok"):
        data = response.get("data", {})
        lg = st.session_state.language_generator
        resumen = lg.generar_respuesta(accion, data)

        st.chat_message("assistant").write(resumen["texto"])

        # Visualización de resultados
        if isinstance(data, dict) and "tabla" in data:
            st.dataframe(data["tabla"], use_container_width=True)
        elif isinstance(data, list):
            st.dataframe(data, use_container_width=True)
        else:
            st.write(data)

        st.session_state.context_manager.update(
            key="ultima_respuesta",
            value=resumen["texto"],
            metadata={"accion": accion, "parametros": parametros}
        )

    else:
        fb = st.session_state.fallback_manager
        respuesta = fb.handle(
            user_input,
            response.get("error", "Error desconocido"),
            tipo="n8n",
            accion=accion,
            parametros=parametros
        )
        st.chat_message("assistant").error(respuesta["texto"])
        st.session_state.context_manager.update(
            key="ultima_respuesta",
            value=respuesta["texto"],
            metadata=respuesta
        )

# ------------------------------------------------------------
#  MODO DEBUG (DETALLES DE SESIÓN)
# ------------------------------------------------------------
if debug_mode:
    st.markdown("---")
    st.markdown("### 🩺 Depuración activa")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧠 Context Manager")
        st.json(st.session_state.context_manager.context)

    with col2:
        st.subheader("🪵 Últimos fallbacks")
        st.json(st.session_state.fallback_manager.leer_log(5))
