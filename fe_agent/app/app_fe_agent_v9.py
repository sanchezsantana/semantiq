# ============================================================
#  app_fe_agent_v9.py
#  Agente FE — Visualización avanzada con Matplotlib y Plotly
# ============================================================

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import streamlit as st
import pandas as pd

from core.context_manager_v3 import ContextManager
from core.llm_interpreter_v3 import LLMInterpreterV3
from core.n8n_connector_v3 import N8NConnectorV3
from core.ambiguity_manager_v3 import AmbiguityManagerV3
from core.disambiguation_manager_v2 import DisambiguationManagerV2
from core.hypothesis_router_v1 import HypothesisRouterV1
from core.render_visualization import VisualizationRenderer

# ------------------------------------
# INIT
# ------------------------------------
st.set_page_config(page_title="Agente FE v9", layout="wide")
st.title("🧠 Agente FE — Asistente de Análisis Comercial Inteligente")

# Managers
if "cm" not in st.session_state:
    st.session_state.cm = ContextManager(persist_path="data/session.json")
if "llm" not in st.session_state:
    st.session_state.llm = LLMInterpreterV3(
        llm_url="http://localhost:11434/api/generate",
        model="gemma:2b",
        prompt_file="data/FE_prompt_instruccional_v4.json"
    )
if "n8n" not in st.session_state:
    st.session_state.n8n = N8NConnectorV3()
if "amb" not in st.session_state:
    st.session_state.amb = AmbiguityManagerV3()
if "dis" not in st.session_state:
    st.session_state.dis = DisambiguationManagerV2()
if "hyp" not in st.session_state:
    st.session_state.hyp = HypothesisRouterV1()
if "viz" not in st.session_state:
    st.session_state.viz = VisualizationRenderer()

cm, llm, n8n, amb, dis, hyp, viz = (
    st.session_state.cm,
    st.session_state.llm,
    st.session_state.n8n,
    st.session_state.amb,
    st.session_state.dis,
    st.session_state.hyp,
    st.session_state.viz,
)

# Sidebar
with st.sidebar:
    st.subheader("⚙️ Configuración del Asistente")
    st.markdown("Este asistente te ayuda a analizar tus **ventas**, **compras**, **clientes** y **stock** usando IA.")
    backend = st.selectbox(
        "Motor de visualización",
        ["streamlit", "matplotlib", "plotly"],
        index=0
    )
    st.info(f"Backend actual: {backend}")
    st.markdown("**Modo gráfico:** adaptativo según acción o preferencia del usuario.")

# ------------------------------------
# INTERFAZ PRINCIPAL
# ------------------------------------
user_input = st.chat_input("Soy tu asistente de análisis de compra-venta. ¿En qué te puedo ayudar hoy?")

if user_input:
    st.chat_message("user").markdown(user_input)

    # 1️⃣ Detectar ambigüedad o fuera de dominio
    amb_eval = amb.procesar_input(user_input)
    if amb_eval.get("requiere_clarificacion"):
        tipo = amb_eval.get("tipo")
        motivo = amb_eval.get("mensaje")

        if tipo in ("clarify", "out_of_scope"):
            ctx = cm.to_llm_context(limit_historial=6)
            clar = dis.clarify(user_input, ctx)
            status = clar.get("status")
            q = clar.get("clarification_question")
            reph = clar.get("rephrased_question")

            if status == "out_of_scope":
                st.chat_message("assistant").markdown(
                    q or "Esa pregunta parece fuera del dominio de la ferretería."
                )
                st.stop()

            if q:
                st.chat_message("assistant").markdown(q)
                cm.update("clarificacion_pendiente", q)
            if reph:
                st.chat_message("assistant").markdown(f"¿Te refieres a: *{reph}*?")
            st.stop()

    # 2️⃣ Interpretación normal
    parsed = llm.interpret(user_input, cm.to_llm_context())
    accion, params = parsed.get("accion"), parsed.get("parametros")
    visual = parsed.get("visualizacion_sugerida", "")

    # 3️⃣ Ejecutar acción
    result = n8n.execute(accion, params)
    data = result.get("data")
    ok = result.get("ok", False)

    if not ok:
        st.chat_message("assistant").markdown("No se pudo ejecutar la acción solicitada.")
        st.stop()

    # 4️⃣ Mostrar resultado + visualización
    if isinstance(data, dict) and "tabla" in data:
        df = pd.DataFrame(data["tabla"])
        st.dataframe(df)
        cm.update("ultima_tabla", data["tabla"])

        if visual:
            st.chat_message("assistant").markdown(
                f"Generando gráfico sugerido: **{visual}** ({backend})"
            )
            viz.render(df, visual, backend=backend)
    else:
        st.chat_message("assistant").markdown(str(data))

    cm.update_last_action(accion)
    cm.save_to_file()
