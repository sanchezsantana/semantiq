# ============================================================
#  app_fe_agent_v7.py
#  Agente FE — Visualización Cognitiva y Empática
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-30
# ============================================================

import streamlit as st
import pandas as pd
import json
import requests
from typing import Dict, Any

# Núcleo Semantiq
from core.context_manager_v3 import ContextManager
from core.llm_interpreter_v3 import LLMInterpreterV3
from core.n8n_connector_v3 import N8NConnectorV3
from core.ambiguity_manager_v2 import AmbiguityManagerV2


# ============================================================
#  CONFIGURACIÓN INICIAL
# ============================================================

st.set_page_config(page_title="Agente FE - Semantiq", layout="wide")

st.title("🧠 Agente FE — Ferretería Inteligente (Semantiq)")
st.caption("Versión 7 — Visualización cognitiva y empática, sin botones")

# Inicialización de módulos
if "context_manager" not in st.session_state:
    st.session_state.context_manager = ContextManager(persist_path="data/session_log.json")
if "llm_interpreter" not in st.session_state:
    st.session_state.llm_interpreter = LLMInterpreterV3(
        llm_url="http://localhost:11434/api/generate",
        model="gemma:2b",
        prompt_file="data/FE_prompt_instruccional_v2.json"
    )
if "n8n_connector" not in st.session_state:
    st.session_state.n8n_connector = N8NConnectorV3()
if "ambiguity_manager" not in st.session_state:
    st.session_state.ambiguity_manager = AmbiguityManagerV2()

# Alias cortos
cm: ContextManager = st.session_state.context_manager
llm: LLMInterpreterV3 = st.session_state.llm_interpreter
n8n: N8NConnectorV3 = st.session_state.n8n_connector
am: AmbiguityManagerV2 = st.session_state.ambiguity_manager


# ============================================================
#  FUNCIÓN AUXILIAR: Resolver tipo de gráfico con empatía
# ============================================================

def resolver_tipo_grafico(accion: str, preferencia_usuario: str, sugerido_llm: str) -> Dict[str, Any]:
    """Determina el tipo de gráfico final y genera un mensaje empático de respuesta."""

    tipos_validos = {
        "consultar_tendencia_ventas": ["líneas", "barras"],
        "obtener_top_productos_vendidos": ["barras", "torta"],
        "consultar_margen_global": ["barras", "columnas"],
        "consultar_relacion_compras_ventas": ["columnas", "barras"],
        "consultar_total_ventas": ["barras", "columnas"],
    }

    preferencia_usuario = (preferencia_usuario or "").lower().strip()
    sugerido_llm = (sugerido_llm or "").lower().strip()
    opciones = tipos_validos.get(accion, ["barras"])

    # Caso 1: usuario pide algo válido
    if preferencia_usuario in opciones:
        return {
            "tipo": preferencia_usuario,
            "mensaje_agente": f"Perfecto, te muestro el gráfico en formato de {preferencia_usuario} como prefieres."
        }

    # Caso 2: usuario pide algo no óptimo
    alternativas = ", ".join(opciones)
    return {
        "tipo": sugerido_llm if sugerido_llm in opciones else opciones[0],
        "mensaje_agente": (
            f"Entiendo que prefieres un gráfico de {preferencia_usuario}, "
            f"pero ese tipo de visualización se usa mejor en otros contextos. "
            f"En este caso te sugiero {alternativas}, que permiten ver mejor la información."
        )
    }


# ============================================================
#  BARRA LATERAL
# ============================================================

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


# ============================================================
#  PROCESAMIENTO PRINCIPAL
# ============================================================

st.divider()
user_input = st.chat_input("Haz una pregunta sobre ventas, compras o márgenes...")

if user_input:
    st.chat_message("user").markdown(user_input)

    # 1️⃣ Detección de ambigüedad
    amb = am.procesar_input(user_input, cm)
    if amb["requiere_clarificacion"]:
        st.chat_message("assistant").markdown(amb["mensaje"])
        cm.update("clarificacion_pendiente", amb["mensaje"])
    else:
        # 2️⃣ Obtener contexto y enviar al LLM
        context_for_llm = cm.to_llm_context(limit_historial=5)
        parsed = llm.interpret(user_input, context_for_llm)
        accion = parsed.get("accion", "fallback")
        parametros = parsed.get("parametros", {})
        visual_sugerida = parsed.get("visualizacion_sugerida", "")

        cm.update_last_action(accion)

        # 3️⃣ Ejecución en n8n
        result = n8n.execute(accion, parametros)
        data = result.get("data", {})
        ok = result.get("ok", False)

        if not ok:
            st.chat_message("assistant").markdown(data.get("mensaje", "No se pudo ejecutar la acción."))
        else:
            st.chat_message("assistant").markdown(f"**Acción interpretada:** `{accion}`")

            # 4️⃣ Visualización empática y cognitiva
            if isinstance(data, dict) and "tabla" in data:
                df = pd.DataFrame(data["tabla"])
                st.dataframe(df)
                cm.update("ultima_tabla", data["tabla"])
                cm.mark_graph_pending(data["tabla"])

                # Determinar si el usuario ya pidió gráfico en su texto
                user_lower = user_input.lower()
                quiere_grafico = any(w in user_lower for w in ["grafico", "gráfico", "visualiza", "ver en barras", "mostrar en barras", "mostrar gráfico"])

                # Extraer preferencia específica del usuario si existe
                tipo_preferencia = None
                for tipo in ["barras", "líneas", "lineas", "torta", "columnas"]:
                    if tipo in user_lower:
                        tipo_preferencia = tipo
                        break

                if cm.get("preferencia_visual") == "nunca":
                    quiere_grafico = False
                elif cm.get("preferencia_visual") == "siempre":
                    quiere_grafico = True

                # Caso 1: Usuario explícito → mostrar
                if quiere_grafico:
                    resolved = resolver_tipo_grafico(accion, tipo_preferencia, visual_sugerida)
                    st.chat_message("assistant").markdown(resolved["mensaje_agente"])
                    try:
                        tipo_final = resolved["tipo"]
                        if "barra" in tipo_final:
                            st.bar_chart(df.set_index(df.columns[0]))
                        elif "línea" in tipo_final or "linea" in tipo_final:
                            st.line_chart(df.set_index(df.columns[0]))
                        elif "torta" in tipo_final or "pie" in tipo_final:
                            st.pyplot(df.plot.pie(y=df.columns[1], legend=False).figure)
                        else:
                            st.info("Tipo de gráfico no reconocido.")
                    except Exception as e:
                        st.warning(f"No se pudo generar el gráfico: {e}")

                # Caso 2: Visual sugerida pero usuario no pidió → sugerir
                elif visual_sugerida and cm.get("preferencia_visual") != "nunca":
                    st.chat_message("assistant").markdown(
                        f"Puedo mostrarte este resultado también como gráfico de {visual_sugerida.lower()}. "
                        "¿Quieres que lo visualice?"
                    )
                    cm.mark_graph_pending(data["tabla"])

            else:
                st.write(data)

        # 5️⃣ Actualizar historial
        cm.update(metadata={
            "pregunta": user_input,
            "respuesta": data,
            "metadata": {"accion": accion, "parametros": parametros}
        })
        cm.save_to_file()


# ============================================================
#  DIAGNÓSTICO DE SESIÓN
# ============================================================
st.divider()
with st.expander("📜 Resumen de sesión (últimos turnos)"):
    st.json(cm.to_llm_context(limit_historial=5))
