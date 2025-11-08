# ============================================================
#  app_fe_agent_v5.py
#  Versión 5 (gráficos conversacionales)
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-29
# ============================================================

import streamlit as st
import json
import os
import time
from datetime import datetime
import pandas as pd

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
#  CONFIGURACIÓN DE ENTORNOS Y UTILIDADES
# ------------------------------------------------------------
SESSION_LOG_PATH = "data/session_log.json"
ACTION_ROUTER_PATH = "data/FE_action_router.json"

def _safe_context_load(cm: ContextManager):
    """Carga persistencia si existe."""
    if hasattr(cm, "load_from_file"):
        try:
            cm.load_from_file(SESSION_LOG_PATH)
            return
        except:
            pass
    if os.path.exists(SESSION_LOG_PATH):
        with open(SESSION_LOG_PATH, "r", encoding="utf-8") as f:
            snapshot = json.load(f)
        cm.context = snapshot.get("context", {})

def _safe_context_save(cm: ContextManager):
    """Guarda persistencia si existe."""
    if hasattr(cm, "save_to_file"):
        try:
            cm.save_to_file(SESSION_LOG_PATH)
            return
        except:
            pass
    os.makedirs(os.path.dirname(SESSION_LOG_PATH), exist_ok=True)
    snapshot = {"timestamp": datetime.now().isoformat(), "context": cm.context}
    with open(SESSION_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

def _schema_ok(resp: dict) -> bool:
    if not isinstance(resp, dict):
        return False
    if "ok" not in resp:
        return False
    if resp.get("ok") and "data" not in resp:
        return False
    return True

def _execute_n8n_with_retries(conn: N8NConnector, accion: str, parametros: dict, retries: int = 3, delay_s: float = 1.0):
    last_error = None
    for intento in range(1, retries + 1):
        try:
            st.chat_message("assistant").write(f"Intento {intento}/{retries} ejecutando **{accion}**…")
            resp = conn.execute(accion, parametros)
            if _schema_ok(resp):
                return resp
            else:
                last_error = ValueError("Esquema inválido en respuesta de n8n.")
        except Exception as e:
            last_error = e
        if intento < retries:
            time.sleep(delay_s)
    return {"ok": False, "error": str(last_error) if last_error else "Fallo desconocido"}

def _generate_text_with_templates(lg: LanguageGenerator, accion: str, data: dict) -> dict:
    if hasattr(lg, "generar_respuesta"):
        try:
            out = lg.generar_respuesta(accion, data)
            if isinstance(out, dict) and "texto" in out:
                return out
        except Exception as e:
            print(f"[v5] Warning en LanguageGenerator.generar_respuesta: {e}")

    texto = "Acción completada."
    accion_l = (accion or "").lower()
    if "margen" in accion_l:
        texto = f"Margen global: {data.get('margen','N/D')}% sobre ventas de {data.get('ventas','N/D')}."
    elif "ventas" in accion_l:
        texto = f"Ventas totales del período: {data.get('total','N/D')}."
    elif "clientes" in accion_l:
        tabla = data.get("tabla") or []
        texto = f"Se identificaron {len(tabla)} clientes en el período consultado."
    elif "productos" in accion_l:
        texto = "Se listan los productos más relevantes del período consultado."
    elif "proveedores" in accion_l:
        texto = "Se listan los principales proveedores por gasto o volumen."
    return {"texto": texto}

# ------------------------------------------------------------
#  CONFIGURACIÓN DE PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="Agente FE - Ferretería Inteligente", layout="wide")
st.title("🤖 Agente FE - Ferretería Inteligente (v5)")
st.caption("Versión con gráficos conversacionales y mejoras cognitivas.")

# ------------------------------------------------------------
#  INICIALIZACIÓN DE SESIÓN
# ------------------------------------------------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.chat_history = []

    st.session_state.ambiguity_manager = AmbiguityManager()
    st.session_state.llm_interpreter = LLMInterpreter()
    st.session_state.language_generator = LanguageGenerator()
    st.session_state.n8n_connector = N8NConnector(ACTION_ROUTER_PATH)
    st.session_state.context_manager = ContextManager()
    st.session_state.fallback_manager = FallbackManager()

    _safe_context_load(st.session_state.context_manager)
    st.toast("Agente FE inicializado correctamente ✅")

# ------------------------------------------------------------
#  SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Opciones del agente")
    if st.button("🧹 Reiniciar sesión"):
        st.session_state.chat_history = []
        st.session_state.context_manager.clear()
        st.session_state.fallback_manager.limpiar_log()
        if os.path.exists(SESSION_LOG_PATH):
            open(SESSION_LOG_PATH, "w", encoding="utf-8").close()
        st.success("Conversación y logs reiniciados.")

    debug_mode = st.checkbox("🩺 Modo debug", value=False)

    st.markdown("### 🪵 Fallbacks recientes")
    logs = st.session_state.fallback_manager.leer_log(5)
    for item in logs:
        st.caption(f"{item['timestamp']} — {item['tipo']}: {item['motivo']}")

    st.markdown("---")
    st.caption(f"Versión: v5 | {datetime.now().strftime('%d-%m-%Y %H:%M')}")

# ------------------------------------------------------------
#  INTERFAZ PRINCIPAL
# ------------------------------------------------------------
st.markdown("---")
user_input = st.chat_input("Escribe tu consulta o análisis...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    cm = st.session_state.context_manager

    # Si hay una pregunta pendiente de gráfico
    if cm.context.get("grafico_pendiente"):
        if user_input.lower().strip() in ["si", "sí", "claro", "por favor"]:
            data_tabla = cm.context.get("ultima_tabla", [])
            if data_tabla:
                df = pd.DataFrame(data_tabla)
                st.chat_message("assistant").write("Aquí tienes el gráfico solicitado 📊")
                st.bar_chart(df.set_index(df.columns[0]))
            cm.update("grafico_pendiente", False)
            _safe_context_save(cm)
            st.stop()
        elif user_input.lower().strip() in ["no", "no gracias"]:
            st.chat_message("assistant").write("Perfecto, seguimos sin gráfico.")
            cm.update("grafico_pendiente", False)
            _safe_context_save(cm)
            st.stop()

    # Detección si el usuario pide un gráfico explícitamente
    solicita_grafico = any(p in user_input.lower() for p in ["gráfico", "grafico", "visual", "visualiza"])
    cm.update("solicita_grafico", solicita_grafico)

    # 1️⃣ Ambigüedad + fallback
    am = st.session_state.ambiguity_manager
    amb = am.procesar_input(user_input)
    if amb.get("requiere_clarificacion"):
        fb = st.session_state.fallback_manager
        resp = fb.handle(user_input, "Ambigüedad detectada", tipo="ambiguous")
        st.chat_message("assistant").warning(f"{amb['mensaje']} {resp['texto']}")
        cm.update("clarificacion_pendiente", amb.get("mensaje"))
        _safe_context_save(cm)
        st.stop()

    # 2️⃣ Interpretación
    llm = st.session_state.llm_interpreter
    parsed = llm.interpret(amb.get("mensaje", user_input))
    if debug_mode:
        with st.expander("🧩 JSON interpretado"):
            st.json(parsed)
    accion = (parsed or {}).get("accion")
    parametros = (parsed or {}).get("parametros", {})

    if not accion:
        fb = st.session_state.fallback_manager
        resp = fb.handle(user_input, "Sin acción detectada", tipo="llm")
        st.chat_message("assistant").warning(resp["texto"])
        cm.update("ultima_respuesta", resp["texto"])
        _safe_context_save(cm)
        st.stop()

    # 3️⃣ Ejecución n8n
    st.chat_message("assistant").write(f"⚙️ Ejecutando acción: **{accion}**")
    response = _execute_n8n_with_retries(st.session_state.n8n_connector, accion, parametros)
    if not response.get("ok"):
        fb = st.session_state.fallback_manager
        resp = fb.handle(user_input, response.get("error", "Error desconocido"), tipo="n8n", accion=accion)
        st.chat_message("assistant").error(resp["texto"])
        cm.update("ultima_respuesta", resp["texto"])
        _safe_context_save(cm)
        st.stop()

    # 4️⃣ Procesamiento
    data = response.get("data", {}) or {}
    resumen = _generate_text_with_templates(st.session_state.language_generator, accion, data)
    st.chat_message("assistant").write(resumen["texto"])

    # Mostrar tabla y decidir sobre gráfico
    if isinstance(data, dict) and "tabla" in data and isinstance(data["tabla"], (list, tuple)):
        try:
            df = pd.DataFrame(data["tabla"])
            st.dataframe(df, use_container_width=True)
            cm.update("ultima_tabla", data["tabla"])
            _safe_context_save(cm)
            if cm.context.get("solicita_grafico"):
                st.chat_message("assistant").write("Generando el gráfico solicitado 📈…")
                st.bar_chart(df.set_index(df.columns[0]))
            else:
                st.chat_message("assistant").write("¿Deseas que te muestre un gráfico con esta información? (responde 'sí' o 'no')")
                cm.update("grafico_pendiente", True)
                _safe_context_save(cm)
        except Exception as e:
            st.warning(f"No fue posible mostrar la tabla: {e}")

    cm.update("ultima_respuesta", resumen.get("texto", ""))
    _safe_context_save(cm)

# ------------------------------------------------------------
#  MODO DEBUG
# ------------------------------------------------------------
if 'debug_mode' in locals() and debug_mode:
    st.markdown("---")
    st.markdown("### 🔍 Depuración activa")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Context Manager")
        st.json(st.session_state.context_manager.context)
    with col2:
        st.subheader("Fallbacks recientes")
        st.json(st.session_state.fallback_manager.leer_log(5))

