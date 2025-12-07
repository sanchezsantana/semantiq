import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(page_title="K9 Mining Safety", layout="wide")

# ============================================================
# CSS: AJUSTE SEGURO DE ANCHO A 800 PX (NO ROMPE EL LAYOUT)
# ============================================================
st.markdown("""
<style>
    .block-container {
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }

    .main-block {
        padding-bottom: 80px;
    }

    .user-bubble {
        background-color: #444;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 6px;
        display: inline-block;
        max-width: 85%;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ESTADO GLOBAL
# ============================================================
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "pending_graph" not in st.session_state:
    st.session_state["pending_graph"] = False

DELAY_SIMPLE = 2.0
DELAY_RANKING = 2.8
DELAY_NARRATIVE = 3.2

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def load_data():
    df_signals = pd.read_parquet("data/k9_weekly_signals.parquet")
    df_proactivo = pd.read_csv("data/stde_proactivo_semanal_v4_4.csv")
    df_tray = pd.read_csv("data/stde_trayectorias_semanales.csv")
    df_events = pd.read_csv("data/stde_eventos.csv")
    df_obs = pd.read_csv("data/stde_observaciones_12s.csv")
    df_aud = pd.read_csv("data/stde_auditorias_12s.csv")
    return df_signals, df_proactivo, df_tray, df_events, df_obs, df_aud

df_signals, df_proactivo, df_tray, df_events, df_obs, df_aud = load_data()

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("K9 Mining Safety")
st.sidebar.markdown("### *CMAS – Cognitive Multi-Agent System*")
st.sidebar.markdown("---")

st.sidebar.markdown("#### Historial de preguntas")

for i, msg in enumerate([m for m in st.session_state["messages"] if m["role"] == "user"], start=1):
    st.sidebar.markdown(f"{i}. {msg['content']}")

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def plot_r02():
    df_r = df_signals[df_signals["riesgo_id"] == "R02"]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df_r["semana"], df_r["score"], color="orange", marker="o")
    ax.set_title("Evolución semanal: R02")
    ax.set_xlabel("Semana")
    ax.set_ylabel("Score K9")
    st.pyplot(fig)

def narrative_last_month():
    st.markdown("""
### Análisis Narrativo del Último Mes – R01 y R02
- R01 muestra señales emergentes previas al lunes crítico.
- R02 se mantiene dominante.
- Observaciones y auditorías refuerzan estas tendencias.
""")

def get_proactive_ranking():
    wk = df_proactivo["semana_id"].max()
    df_last = df_proactivo[df_proactivo["semana_id"] == wk].copy()
    df_last = df_last.sort_values("score_proactivo", ascending=False)
    df_last["Ranking"] = range(1, len(df_last) + 1)
    df_last = df_last.set_index("Ranking")
    return wk, df_last

def get_observations_last_week():
    wk = df_obs["semana"].max()
    df_last = df_obs[df_obs["semana"] == wk]
    total = len(df_last)
    opg = sum(df_last["tipo_observacion"] == "OPG")
    occ = sum(df_last["tipo_observacion"] == "OCC")
    return wk, total, opg, occ

# ============================================================
# DESPACHADOR CON REASONING DETALLADO (YAML-LIKE)
# ============================================================
def handle_query(query):
    q = query.lower()

    # ============================
    # FUERA DE DOMINIO
    # ============================
    if "capital" in q and "chile" in q:
        reasoning = """reasoning:
  dominio: fuera_del_alcance
  acción: rechazar_pregunta
"""
        return ("Esa pregunta está fuera del dominio del sistema.", reasoning,
                False, False, False)

    # ============================
    # OBSERVACIONES
    # ============================
    if "observacion" in q or "observaciones" in q:
        wk, total, opg, occ = get_observations_last_week()

        reasoning = f"""reasoning:
  input: observaciones_semana
  operations:
    - obtener_semana_actual := {wk}
    - filtrar(semana = semana_actual)
    - contar_total
    - contar_por_tipo(OPG, OCC)
  output:
    total: {total}
    opg: {opg}
    occ: {occ}
"""
        return (f"En la semana {wk} hubo **{total} observaciones** (OPG: {opg}, OCC: {occ}).",
                reasoning, False, False, False)

    # ============================
    # RANKING PROACTIVO
    # ============================
    if "ranking" in q:
        wk, _ = get_proactive_ranking()

        reasoning = f"""reasoning:
  input: ranking_proactivo
  operations:
    - obtener_semana_actual := {wk}
    - filtrar(semana = semana_actual)
    - ordenar(score_proactivo DESC)
    - asignar_ranking(1..n)
"""
        return (f"Este es el ranking de riesgos de la semana {wk}.",
                reasoning, False, True, False)

    # ============================
    # RIESGO MÁS IMPORTANTE
    # ============================
    if "riesgo más importante" in q or "riesgo mas importante" in q:
        wk = df_signals["semana"].max()
        df_w = df_signals[df_signals["semana"] == wk]
        r_top = df_w.sort_values("score", ascending=False).iloc[0]["riesgo_id"]

        st.session_state["pending_graph"] = True

        reasoning = f"""reasoning:
  input: señales_semana
  operations:
    - semana_actual := {wk}
    - filtrar(semana = semana_actual)
    - ordenar(score DESC)
    - seleccionar_top(1)
  output:
    riesgo_mas_importante: {r_top}
"""
        return (f"El riesgo más importante esta semana es **{r_top}**. ¿Deseas ver un gráfico?",
                reasoning, False, False, False)

    # ============================
    # GRÁFICO
    # ============================
    if "grafico" in q or "gráfico" in q or (
        q.strip().lower() in ["si", "sí"] and st.session_state["pending_graph"]
    ):
        st.session_state["pending_graph"] = False

        reasoning = """reasoning:
  input: señales(R02)
  operations:
    - extraer_series_temporales
    - generar_grafico_linea
"""
        return ("Aquí tienes la evolución del riesgo R02.", reasoning,
                True, False, False)

    # ============================
    # NARRATIVA
    # ============================
    if "narrativ" in q or "último mes" in q or "ultimo mes" in q:

        reasoning = """reasoning:
  input: señales(R01, R02), observaciones, auditorías
  operations:
    - analizar_tendencias
    - detectar_patrones
    - generar_resumen_narrativo
"""
        return ("Aquí tienes la narrativa del último mes para R01 y R02.",
                reasoning, False, False, True)

    # ============================
    # DEFAULT
    # ============================
    reasoning = """reasoning:
  acción: fallback
  opciones_validas:
    - ranking
    - riesgo más importante
    - observaciones
    - narrativa
"""
    return ("Puedo ayudarte con: ranking, riesgo más importante, observaciones o narrativa.",
            reasoning, False, False, False)

# ============================================================
# BLOQUE PRINCIPAL DEL CHAT
# ============================================================
st.markdown('<div class="main-block">', unsafe_allow_html=True)
st.markdown("### Conversación")

for msg in st.session_state["messages"]:
    st.markdown("---")

    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-bubble"><strong>Pregunta:</strong> {msg["content"]}</div>',
            unsafe_allow_html=True
        )

    else:
        with st.expander("Ver reasoning (nodo cognitivo)"):
            st.text(msg["reasoning"])

        st.markdown(f"**Respuesta:** {msg['content']}")

        if msg.get("show_rank"):
            wk, df_rank = get_proactive_ranking()
            st.dataframe(df_rank, use_container_width=True)

        if msg.get("show_plot"):
            plot_r02()

        if msg.get("show_narrative"):
            narrative_last_month()

st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# INPUT FIJO — CHAT NATIVO STREAMLIT
# ============================================================
query = st.chat_input("Escribe tu pregunta:")

if query:
    st.session_state["messages"].append({
        "role": "user",
        "content": query.strip()
    })

    with st.spinner("Procesando..."):
        answer, reasoning, show_plot, show_rank, show_narrative = handle_query(query.strip())

        if show_narrative:
            time.sleep(DELAY_NARRATIVE)
        elif show_plot or show_rank:
            time.sleep(DELAY_RANKING)
        else:
            time.sleep(DELAY_SIMPLE)

    st.session_state["messages"].append({
        "role": "assistant",
        "content": answer,
        "reasoning": reasoning,
        "show_plot": show_plot,
        "show_rank": show_rank,
        "show_narrative": show_narrative,
    })

    st.rerun()

