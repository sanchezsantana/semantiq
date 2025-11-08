# ============================================================
#  core/render_visualization.py
#  Renderizador visual modular (Streamlit + Matplotlib + Plotly)
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-11-01
# ============================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px


class VisualizationRenderer:
    """
    Renderiza tablas y gráficos según el tipo sugerido o preferencia del usuario.
    Compatible con Streamlit, Matplotlib y Plotly.
    """

    def __init__(self):
        self.default_backend = "streamlit"

    # ------------------------------------------------------------
    def render(self, df: pd.DataFrame, tipo: str, backend: str = None):
        """Renderiza un gráfico a partir del tipo especificado."""
        tipo = (tipo or "").lower().strip()
        backend = backend or self.default_backend

        if df is None or df.empty:
            st.warning("No hay datos para graficar.")
            return

        if backend not in ["streamlit", "matplotlib", "plotly"]:
            backend = "streamlit"

        # Normaliza DataFrame para gráficos
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)
        if len(df.columns) < 2:
            st.warning("El dataset requiere al menos dos columnas para graficar.")
            st.dataframe(df)
            return

        # Enrutamiento
        if backend == "streamlit":
            self._render_streamlit(df, tipo)
        elif backend == "matplotlib":
            self._render_matplotlib(df, tipo)
        elif backend == "plotly":
            self._render_plotly(df, tipo)

    # ------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------
    def _render_streamlit(self, df: pd.DataFrame, tipo: str):
        if "barra" in tipo:
            st.bar_chart(df.set_index(df.columns[0]))
        elif "línea" in tipo or "linea" in tipo:
            st.line_chart(df.set_index(df.columns[0]))
        elif "área" in tipo:
            st.area_chart(df.set_index(df.columns[0]))
        else:
            st.dataframe(df)

    def _render_matplotlib(self, df: pd.DataFrame, tipo: str):
        fig, ax = plt.subplots(figsize=(6, 4))

        # Gráfico de torta
        if "torta" in tipo or "pie" in tipo:
            try:
                df.set_index(df.columns[0])[df.columns[1]].plot.pie(
                    autopct="%1.1f%%", ax=ax, legend=False
                )
                ax.set_ylabel("")
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"No se pudo graficar torta: {e}")

        # Gráfico de columnas comparativas
        elif "columna" in tipo or "columnas" in tipo:
            df.plot(kind="bar", ax=ax)
            ax.set_xlabel(df.columns[0])
            ax.set_ylabel(df.columns[1])
            ax.set_title("Comparación de valores")
            st.pyplot(fig)

        else:
            st.dataframe(df)

    def _render_plotly(self, df: pd.DataFrame, tipo: str):
        try:
            if "barras" in tipo or "bar" in tipo:
                fig = px.bar(df, x=df.columns[0], y=df.columns[1], text_auto=True)
            elif "línea" in tipo or "linea" in tipo:
                fig = px.line(df, x=df.columns[0], y=df.columns[1], markers=True)
            elif "torta" in tipo or "pie" in tipo:
                fig = px.pie(df, names=df.columns[0], values=df.columns[1], hole=0.2)
            elif "columna" in tipo or "columnas" in tipo:
                fig = px.bar(df, x=df.columns[0], y=df.columns[1], barmode="group")
            else:
                st.dataframe(df)
                return
            fig.update_layout(
                template="plotly_white",
                title=f"{tipo.title()} interactivo",
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo generar gráfico interactivo: {e}")
