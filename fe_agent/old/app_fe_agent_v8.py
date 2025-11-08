# ============================================================
#  app_fe_agent_v8.py
#  Agente FE - Orquestación cognitiva completa
# ============================================================

import streamlit as st
import pandas as pd

from core.context_manager_v3 import ContextManager
from core.llm_interpreter_v3 import LLMInterpreterV3
from core.n8n_connector_v3 import N8NConnectorV3
from core.ambiguity_manager_v3 import AmbiguityManagerV3
from core.disambiguation_manager_v2 import DisambiguationManagerV2
from core.hypothesis_router_v1 import HypothesisRouterV1
from core.ambiguity_manager_v3 import AmbiguityManagerV3

# ------------------------------------
# INIT
# ------------------------------------
st.set_page_config(page_title="Agente FE v8", layout="wide")
st.title("🧠 Agente FE v8 — Modo cognitivo integral")

# Managers
if "cm" not in st.session_state:
    st.session_state.cm = ContextManager(persist_path="data/session.json")
if "llm" not in st.session_state:
    st.session_state.llm = LLMInterpreterV3(
        llm_url="http://localhost:11434/api/generate",
        model="gemma:2b",
        prompt_file="data/FE_prompt_instruccional_v3.json"
    )
if "n8n" not in st.session_state:
    st.session_state.n8n = N8NConnectorV3()
if "amb" not in st.session_state:
    st.session_state.amb = AmbiguityManagerV3()
if "dis" not in st.session_state:
    st.session_state.dis = DisambiguationManagerV2()
if "hyp" not in st.session_state:
    st.session_state.hyp = HypothesisRouterV1()

cm, llm, n8n, amb, dis, hyp = (
    st.session_state.cm,
    st.session_state.llm,
    st.session_state.n8n,
    st.session_state.amb,
    st.session_state.dis,
    st.session_state.hyp,
)

# ------------------------------------
# INTERFAZ PRINCIPAL
# ------------------------------------
user_input = st.chat_input("Haz tu pregunta...")

if user_input:
    st.chat_message("user").markdown(user_input)

    # 1️⃣ Detección básica de ambigüedad
    amb_eval = amb.procesar_input(user_input)
    if amb_eval.get("requiere_clarificacion"):
        tipo = amb_eval.get("tipo")
        motivo = amb_eval.get("mensaje")

        # Si fuera de dominio o muy ambigua → activar DisambiguationManager
        if tipo in ("clarify", "out_of_scope"):
            ctx = cm.to_llm_context(limit_historial=6)
            clar = dis.clarify(user_input, ctx)
            status = clar.get("status")
            q = clar.get("clarification_question")
            reph = clar.get("rephrased_question")
            cands = clar.get("candidate_intents", [])

            if status == "out_of_scope":
                st.chat_message("assistant").markdown(
                    q or "Esa pregunta parece fuera del dominio de la ferretería. Puedo ayudarte con ventas, compras o stock."
                )
                st.stop()

            if q:
                st.chat_message("assistant").markdown(q)
                cm.update("clarificacion_pendiente", q)

            if cands:
                cm.update("hipotesis_candidatas", cands)

            if reph:
                st.chat_message("assistant").markdown(f"¿Te refieres a: *{reph}*?")
                cm.update("reformulacion_tentativa", reph)

            cm.save_to_file()
            st.stop()

    # 2️⃣ Si hay hipótesis pendientes, procesarlas primero
    cands = cm.get("hipotesis_candidatas")
    if cands:
        top = sorted(cands, key=lambda x: x.get("confidence", 0), reverse=True)[0]
        tipo = hyp.classify(top)

        if tipo == "local":
            res = hyp.run_local(top, cm)
            st.chat_message("assistant").markdown(res["mensaje"])
            cm.update("hipotesis_candidatas", None)
            st.stop()

        elif tipo == "confirm":
            st.chat_message("assistant").markdown("Perfecto, confirmado 👍")
            cm.update("hipotesis_candidatas", None)
            st.stop()

        # Si es n8n, seguir flujo normal (abajo)
        accion, params = top.get("accion"), top.get("parametros")
    else:
        parsed = llm.interpret(user_input, cm.to_llm_context())
        accion, params = parsed.get("accion"), parsed.get("parametros")

    # 3️⃣ Ejecución normal en n8n
    result = n8n.execute(accion, params)
    data = result.get("data")
    ok = result.get("ok", False)

    if not ok:
        st.chat_message("assistant").markdown("No pude obtener información. Revisa los datos o el período.")
        st.stop()

    # 4️⃣ Mostrar resultados (texto o tabla)
    if isinstance(data, dict) and "tabla" in data:
        df = pd.DataFrame(data["tabla"])
        st.dataframe(df)
        cm.update("ultima_tabla", data["tabla"])
    else:
        st.chat_message("assistant").markdown(str(data))

    cm.update_last_action(accion)
    cm.save_to_file()
