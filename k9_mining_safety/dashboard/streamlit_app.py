import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(page_title="K9 Mining Safety", layout="centered")

# Sidebar persistente
st.sidebar.title("K9 Mining Safety")
st.sidebar.markdown("### *CMAS – Cognitive Multi-Agent System*")

# Estado global
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "pending_graph" not in st.session_state:
    st.session_state["pending_graph"] = False
if "user_input" not in st.session_state:
    st.session_state["user_input"] = ""
if "clear_input" not in st.session_state:
    st.session_state["clear_input"] = False

# Delays realistas
DELAY_SIMPLE = 2.3
DELAY_RANKING_OR_PLOT = 2.8
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
# FUNCIONES AUXILIARES
# ============================================================
def plot_r02():
    df_r = df_signals[df_signals["riesgo_id"] == "R02"]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df_r["semana"], df_r["score"], marker="o", label="R02", color="orange")
    ax.set_title("Evolución Semanal – R02 (Score K9)")
    ax.set_xlabel("Semana")
    ax.set_ylabel("Score K9")
    ax.legend()
    st.pyplot(fig)


def narrative_last_month():
    st.markdown("""
### Análisis Narrativo del Último Mes – R01 y R02

Durante el último mes, K9 analizó la evolución de los riesgos R01 y R02 integrando
señales semanales, score K9, observaciones, auditorías y factores operacionales.

---

#### R01 – Señales emergentes
- Tendencia ascendente leve pero sostenida.
- Varias observaciones OCC indican presión creciente.
- El modelo proactivo tiende a subestimarlo, pero K9 detecta señales finas.

#### R02 – Riesgo dominante
- Continúa como el riesgo más crítico.
- Score K9 consistentemente alto.
- Influido por congestión, variabilidad y dotación.

---

**Conclusión:**  
K9 combina análisis granular y agregado para entregar una interpretación coherente del estado real.
""")


def get_proactive_ranking():
    last_week = df_proactivo["semana"].max()
    df_last = df_proactivo[df_proactivo["semana"] == last_week].copy()

    # Ordenar por score del modelo proactivo
    score_col = [c for c in df_last.columns if "score" in c.lower()][0]
    df_last = df_last.sort_values(score_col, ascending=False)

    df_last["Ranking"] = range(1, len(df_last) + 1)
    df_last = df_last.set_index("Ranking")

    return last_week, df_last


def get_observations_last_week():
    last_week = df_obs["semana"].max()
    df_last = df_obs[df_obs["semana"] == last_week]
    total = len(df_last)
    n_opg = (df_last["tipo_observacion"] == "OPG").sum()
    n_occ = (df_last["tipo_observacion"] == "OCC").sum()
    return last_week, total, n_opg, n_occ


# ============================================================
# DESPACHADOR DE CONSULTAS
# ============================================================
def handle_query(query: str):
    q = query.lower()
    show_plot = False
    show_ranking = False
    show_narrative = False

    # -------------------
    # Fuera de dominio
    # -------------------
    if "capital" in q and "chile" in q:
        answer = (
            "K9 está especializado exclusivamente en análisis cognitivo de seguridad operacional "
            "y no responde preguntas generales fuera de ese dominio."
        )
        reasoning = (
            "La consulta está fuera del dominio del STDE, la ontología y el modelo cognitivo K9."
        )
        return answer, reasoning, show_plot, show_ranking, show_narrative

    # -------------------
    # Observaciones última semana
    # -------------------
    if "observacion" in q or "observaciones" in q:
        last_week, total, n_opg, n_occ = get_observations_last_week()
        answer = (
            f"En la semana {last_week} se registraron **{total} observaciones**: "
            f"**{n_opg} OPG** y **{n_occ} OCC**."
        )
        reasoning = (
            "Filtro la tabla de observaciones para la semana más reciente "
            "y calculo el total y su composición por tipo."
        )
        return answer, reasoning, show_plot, show_ranking, show_narrative

    # -------------------
    # Ranking modelo proactivo
    # -------------------
    if "ranking" in q and "riesgo" in q:
        last_week, _ = get_proactive_ranking()
        answer = (
            f"A continuación se muestra el ranking de riesgos para la semana {last_week}, "
            "según el modelo proactivo v4.4."
        )
        reasoning = (
            "Selecciono la última semana del archivo proactivo, ordeno por score "
            "y construyo el ranking total de riesgos."
        )
        show_ranking = True
        return answer, reasoning, show_plot, show_ranking, show_narrative

    # -------------------
    # Riesgo más importante
    # -------------------
    if "riesgo más importante" in q or "riesgo mas importante" in q:
        last_week = df_signals["semana"].max()
        df_last = df_signals[df_signals["semana"] == last_week]
        r_top = df_last.sort_values("score", ascending=False).iloc[0]["riesgo_id"]

        st.session_state["pending_graph"] = True

        answer = (
            f"El riesgo más importante en la semana {last_week} es **{r_top}**.  \n"
            "¿Quieres ver un gráfico con su evolución?"
        )
        reasoning = (
            "Ordeno los riesgos por Score K9 para la última semana y selecciono el valor más alto."
        )
        return answer, reasoning, show_plot, show_ranking, show_narrative

    # -------------------
    # Solicitud de gráfico
    # -------------------
    if ("grafico" in q or "gráfico" in q) or (
        (q.strip() == "si" or q.strip() == "sí")
        and st.session_state.get("pending_graph", False)
    ):
        st.session_state["pending_graph"] = False
        answer = "Aquí tienes la evolución del riesgo R02."
        reasoning = "Genero un gráfico exclusivo del riesgo más importante, R02."
        show_plot = True
        return answer, reasoning, show_plot, show_ranking, show_narrative

    # -------------------
    # Narrativa mensual
    # -------------------
    if "narrativ" in q or "ultimo mes" in q or "último mes" in q:
        answer = "Aquí tienes el análisis narrativo del último mes para R01 y R02."
        reasoning = "Sintetizo señales, score y tendencias para ambos riesgos en un periodo mensual."
        show_narrative = True
        return answer, reasoning, show_plot, show_ranking, show_narrative

    # -------------------
    # Respuesta por defecto
    # -------------------
    answer = (
        "Puedo ayudarte con el riesgo más importante, el ranking de riesgos, "
        "las observaciones de la última semana o la narrativa mensual de R01 y R02."
    )
    reasoning = "La pregunta no coincide con ninguna ruta de análisis de esta demo."
    return answer, reasoning, show_plot, show_ranking, show_narrative


# ============================================================
# INPUT DEL USUARIO (arriba, estilo chat GPT)
# ============================================================

# Limpiar input ANTES de renderizar
if st.session_state.get("clear_input", False):
    st.session_state["user_input"] = ""
    st.session_state["clear_input"] = False

query = st.text_input("Escribe tu pregunta:", key="user_input")
submit = st.button("Enviar")

if submit and query.strip():
    st.session_state["messages"].append({"role": "user", "content": query.strip()})

    with st.spinner("Procesando..."):
        answer, reasoning, show_plot, show_ranking, show_narrative = handle_query(query.strip())

        if show_narrative:
            time.sleep(DELAY_NARRATIVE)
        elif show_ranking or show_plot:
            time.sleep(DELAY_RANKING_OR_PLOT)
        else:
            time.sleep(DELAY_SIMPLE)

    st.session_state["messages"].append({
        "role": "assistant",
        "content": answer,
        "reasoning": reasoning,
        "show_plot": show_plot,
        "show_ranking": show_ranking,
        "show_narrative": show_narrative
    })

    st.session_state["clear_input"] = True
    st.rerun()


# ============================================================
# HISTORIAL DE MENSAJES (debajo del input)
# ============================================================
st.markdown("### Conversación")

for msg in st.session_state["messages"]:
    st.markdown("---")

    if msg["role"] == "user":
        st.markdown(f"**Pregunta:** {msg['content']}")
    else:
        if msg.get("reasoning"):
            st.markdown(f"*Reasoning:*  \n*{msg['reasoning']}*")
            st.markdown("<hr style='border: 0.5px solid #444444;'>", unsafe_allow_html=True)

        st.markdown(f"**Respuesta:** {msg['content']}")

        if msg.get("show_ranking"):
            _, df_rank = get_proactive_ranking()
            st.dataframe(df_rank, use_container_width=True)

        if msg.get("show_plot"):
            plot_r02()

        if msg.get("show_narrative"):
            narrative_last_month()
