# ============================================================
#  app_fe_agent_v6.py
#  Agente FE — Integración completa con FT Simulado y Memoria
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-29
# ============================================================

import streamlit as st
import pandas as pd
import json
import requests

from core.context_manager_v3 import ContextManager
from core.llm_interpreter_v3 import LLMInterpreterV3

# ------------------------------------------------------------
# CONFIGURACIÓN INICIAL
# ------------------------------------------------------------

st.set_page_config(page_title="Agente FE - Semantiq", layout="wide")

st.title("🧠 Agente FE — Ferretería Inteligente (Semantiq)")
st.caption("Versión 6 — Integración completa con FT Simulado y Memoria Persistente")

# Inicializar componentes persistentes
if "context_manager" not in st.session_state:
    st.session_state.context_manager = ContextManager(persist_path="data/session_log.json")
if "llm_interpreter" not in st.session_state:
    st.session_state.llm_interpreter = LLMInterpreterV3(
        llm_url="http://localhost:11434/api/generate",
        model="gemma:2b",
        prompt_file="FE_prompt_instruccional_v2.json"
    )

cm: ContextManager = st.session_state.context_manager
llm: LLMInterpreterV3 = st.session_state.llm_interpreter

# ------------------------------------------------------------
# BARRA LATERAL
# ------------------------------------------------------------

with st.sidebar:
    st.subheader("⚙️ Configuración del Agente")
    user_id = st.text_input("Usuario", cm.get("usuario_id", "anonimo"))
    cm.set_user_id(user_id)

    pref_visual = st.selectbox(
        "Preferencia visual",
        options=["auto", "siempre", "nunca"],
        index=["auto", "siempre", "nunca"].index(cm.get("preferencia_visual", "auto"))
    )
    cm.set_visual_preference(pref_visual)

    if st.button("🧹 Reiniciar contexto"):
        cm.clear()
        st.success("Contexto reiniciado.")

    if st.button("💾 Guardar sesión"):
        cm.save_to_file()
        st.success("Contexto guardado correctamente.")

    st.divider()
    st.markdown("**Última acción:**")
    st.write(cm.get("ultima_accion", "—"))
    st.markdown("**Modo visual:** " + cm.get("preferencia_visual", "auto"))

# ------------------------------------------------------------
# ÁREA DE INTERACCIÓN PRINCIPAL
# ------------------------------------------------------------

st.divider()
user_input = st.chat_input("Haz una pregunta sobre las ventas o compras de la ferretería...")

if user_input:
    st.chat_message("user").markdown(user_input)

    # 1️⃣ Construir contexto y enviar al LLM
    context_for_llm = cm.to_llm_context(limit_historial=5)
    parsed = llm.interpret(user_input, context_for_llm)

    accion = parsed.get("accion", "fallback")
    parametros = parsed.get("parametros", {})
    visual_sugerida = parsed.get("visualizacion_sugerida")

    cm.update_last_action(accion)

    # 2️⃣ Ejecutar acción mediante n8n o fuente local
    try:
        n8n_url = f"http://localhost:5678/webhook/{accion}"
        response = requests.post(n8n_url, json=parametros, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Error ejecutando acción '{accion}': {e}")
        data = {"error": str(e)}

    # 3️⃣ Mostrar resultados
    st.chat_message("assistant").markdown(f"**Acción interpretada:** `{accion}`")

    if isinstance(data, dict) and "tabla" in data:
        df = pd.DataFrame(data["tabla"])
        st.dataframe(df)
        cm.update("ultima_tabla", data["tabla"])

        # 4️⃣ Lógica de visualización condicional
        mostrar_grafico = False

        # Caso 1: usuario pidió gráfico explícitamente en la pregunta
        if any(word in user_input.lower() for word in ["grafico", "visual", "ver en barras", "gráfico"]):
            mostrar_grafico = True

        # Caso 2: preferencia persistente del usuario
        elif cm.get("preferencia_visual") == "siempre":
            mostrar_grafico = True
        elif cm.get("preferencia_visual") == "nunca":
            mostrar_grafico = False

        # Caso 3: modo interactivo
        else:
            cm.mark_graph_pending(data["tabla"])
            mostrar = st.radio(
                "¿Deseas visualizar también este resultado en un gráfico?",
                ["No", "Sí"],
                horizontal=True,
                key=f"visual_radio_{accion}"
            )
            if mostrar == "Sí":
                mostrar_grafico = True
            cm.clear_graph_pending()

        # Render del gráfico si corresponde
        if mostrar_grafico and visual_sugerida:
            st.subheader("📊 Visualización sugerida")
            try:
                if "barras" in visual_sugerida.lower():
                    st.bar_chart(df.set_index(df.columns[0]))
                elif "línea" in visual_sugerida.lower() or "linea" in visual_sugerida.lower():
                    st.line_chart(df.set_index(df.columns[0]))
                elif "torta" in visual_sugerida.lower() or "pie" in visual_sugerida.lower():
                    st.pyplot(df.plot.pie(y=df.columns[1], legend=False).figure)
                else:
                    st.info("Tipo de gráfico no reconocido.")
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico: {e}")
    else:
        st.write(data)

    # 5️⃣ Actualizar historial de conversación
    cm.update(metadata={
        "pregunta": user_input,
        "respuesta": data,
        "metadata": {"accion": accion, "parametros": parametros}
    })
    cm.save_to_file()

# ------------------------------------------------------------
#  ZONA DE DIAGNÓSTICO
# ------------------------------------------------------------
st.divider()
with st.expander("📜 Resumen de sesión (últimos turnos)"):
    st.json(cm.to_llm_context(limit_historial=5))

with st.expander("🧠 Historial completo de conversación"):
    st.json(cm.context.get("historial", []))
