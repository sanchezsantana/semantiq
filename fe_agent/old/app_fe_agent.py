# ================================================================
# 🛠️ app_fe.py — Piloto Ferretería (Versión comentada)
# ================================================================
# Este archivo levanta una interfaz Streamlit que permite explorar:
# 1. Las preguntas predefinidas del agente FE.
# 2. Las instrucciones asociadas a cada pregunta.
# 3. El diccionario de datos (catálogo de tablas y relaciones).
#
# Próximos pasos (una vez probado):
# - Conectar esta interfaz a n8n.
# - Integrar un modelo LLM local (Gemma / Ollama) para responder preguntas reales.
# ================================================================

import json
from pathlib import Path
import streamlit as st

# ---------------------------------------------------------------
# Configuración general de la app (título, ícono, disposición)
# ---------------------------------------------------------------
st.set_page_config(page_title="Piloto Ferretería", page_icon="🛠️", layout="wide")

# Carpeta base donde está este archivo
DATA_DIR = Path(__file__).parent

# Rutas de los archivos JSON del proyecto
F_DICT = DATA_DIR / "ferreteria_modo_ia_diccionario.json"
F_QA   = DATA_DIR / "ferreteria_modo_ia_preguntas_respuestas sin instrucciones.json"
F_TPL  = DATA_DIR / "ferreteria_modo_ia_prompt_template instruccional.json"

# ---------------------------------------------------------------
# Función genérica para cargar archivos JSON de forma segura
# ---------------------------------------------------------------
def load_json(p: Path):
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"No se encontró el archivo: {p.name}")
    except Exception as e:
        st.error(f"Error leyendo {p.name}: {e}")
    return None

# ---------------------------------------------------------------
# Carga de los archivos del proyecto
# ---------------------------------------------------------------
diccionario = load_json(F_DICT)
preguntas   = load_json(F_QA) or []
templates   = load_json(F_TPL) or []

# ---------------------------------------------------------------
# Encabezado principal de la interfaz
# ---------------------------------------------------------------
st.title("🛠️ Piloto FE — Ferretería Inteligente")
st.caption("Interfaz base para explorar preguntas predefinidas, sus respuestas esperadas y el diccionario de datos del negocio.")

# ---------------------------------------------------------------
# Diseño de columnas: menú (izquierda) y detalles (derecha)
# ---------------------------------------------------------------
col1, col2 = st.columns([1, 2])

# ---------------------------------------------------------------
# 🔸 Columna izquierda: selector de preguntas
# ---------------------------------------------------------------
with col1:
    st.subheader("Preguntas disponibles")

    # Crear un diccionario donde la clave visible sea "id + pregunta"
    opciones = {f"{p['id']:02d} — {p['pregunta']}": p for p in preguntas}

    # Selector desplegable de preguntas
    seleccion = st.selectbox(
        "Elige una pregunta:",
        list(opciones.keys())
    ) if opciones else None

    # Mostrar detalles de la pregunta seleccionada
    if seleccion:
        p = opciones[seleccion]
        st.write("**Tipo de respuesta:**", p.get("tipo_respuesta", "No definido"))
        st.write("**Descripción de salida:**", p.get("descripcion_salida", "No definida"))

        # Si la pregunta incluye estructura de tabla o gráfico, mostrarla
        if "estructura_tabla" in p:
            st.write("**Estructura esperada de tabla:**", p["estructura_tabla"])
        if "descripcion_grafico" in p:
            st.write("**Descripción de gráfico sugerido:**", p["descripcion_grafico"])

# ---------------------------------------------------------------
# 🔹 Columna derecha: instrucción asociada al LLM
# ---------------------------------------------------------------
with col2:
    st.subheader("Instrucción para el LLM (modelo de lenguaje)")

    tpl = None
    if seleccion and templates:
        # Buscar el template correspondiente por texto de pregunta
        titulo = opciones[seleccion]["pregunta"]
        for t in templates:
            if t.get("pregunta") == titulo:
                tpl = t
                break

    # Mostrar la instrucción y formato de salida si existe
    if tpl:
        st.code(tpl.get("instruccion_para_LLM", "Sin instrucción definida"), language="markdown")
        st.markdown("**Formato de respuesta ideal:** " + tpl.get("formato_respuesta_ideal", "N/D"))

        # Mostrar ejemplo en Markdown renderizado
        ejemplo = tpl.get("ejemplo_markdown")
        if ejemplo:
            st.markdown("**Ejemplo de salida (markdown renderizado):**")
            st.markdown(ejemplo)
    else:
        st.info("Selecciona una pregunta para ver su instrucción asociada.")

# ---------------------------------------------------------------
# 🔸 Sección inferior: vista rápida del diccionario de datos
# ---------------------------------------------------------------
st.divider()
st.subheader("📚 Diccionario de datos (modelo base del negocio)")

if diccionario:
    with st.expander("Ver esquemas de tablas y campos"):
        for tabla, info in diccionario.items():
            if tabla == "relations":
                continue
            st.markdown(f"**{tabla}** — {info.get('description', '')}")
            campos = info.get("fields", {})
            st.table({"Campo": list(campos.keys()), "Descripción": list(campos.values())})

    # Mostrar relaciones entre entidades
    if "relations" in diccionario:
        st.markdown(f"**Relaciones principales:** `{diccionario['relations']}`")

else:
    st.warning("No se cargó el diccionario. Asegúrate de que el archivo JSON esté en la carpeta del proyecto.")

# ---------------------------------------------------------------
# Pie de página
# ---------------------------------------------------------------
st.caption("Versión base del piloto — Semantiq Framework | Eduardo Sánchez Santana")
