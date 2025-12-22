from typing import List, Dict, Any

import plotly.graph_objects as go
import pandas as pd


def render_metrics(
    analysis: Dict[str, Any],
    visual_suggestions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Metrics Adapter

    Rol:
    - Convertir visual_suggestions (definidas por MetricsNode)
      en artefactos renderizables por Streamlit.
    - NO decidir reglas.
    - NO acceder a data raw externa.
    - NO modificar analysis.

    Retorna:
    - Lista de dicts con:
        {
            "type": "plotly" | "table",
            "figure" | "data": objeto renderizable
        }
    """

    rendered_outputs: List[Dict[str, Any]] = []

    for suggestion in visual_suggestions:
        metric = suggestion.get("metric")
        chart_type = suggestion.get("type")

        # ------------------------------------------------------------------
        # 1. Serie temporal (line_chart)
        # ------------------------------------------------------------------
        if chart_type == "line_chart" and metric == "risk_trajectory":
            trajectories = analysis.get("risk_trajectories", {})

            if not trajectories:
                continue

            fig = go.Figure()

            for risk_id, data in trajectories.items():
                values = data.get("weekly_values", [])
                weeks = list(range(1, len(values) + 1))

                fig.add_trace(
                    go.Scatter(
                        x=weeks,
                        y=values,
                        mode="lines+markers",
                        name=risk_id,
                    )
                )

            fig.update_layout(
                title="Evolución temporal de riesgos",
                xaxis_title="Semana",
                yaxis_title="Índice de riesgo",
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
            )

            rendered_outputs.append(
                {
                    "type": "plotly",
                    "figure": fig,
                }
            )

        # ------------------------------------------------------------------
        # 2. Comparación entre riesgos (bar_chart – risk_comparison)
        # ------------------------------------------------------------------
        elif chart_type == "bar_chart" and metric == "risk_comparison":
            entities = suggestion.get("entities", [])

            if not entities:
                continue

            values = []
            labels = []

            # Se intenta obtener valores representativos desde analysis
            trajectories = analysis.get("risk_trajectories", {})

            for risk_id in entities:
                labels.append(risk_id)

                if risk_id in trajectories:
                    weekly = trajectories[risk_id].get("weekly_values", [])
                    values.append(weekly[-1] if weekly else 0)
                else:
                    values.append(1)  # fallback neutro (comparativo)

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=labels,
                        y=values,
                    )
                ]
            )

            fig.update_layout(
                title="Comparación entre riesgos",
                xaxis_title="Riesgo",
                yaxis_title="Valor relativo",
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
            )

            rendered_outputs.append(
                {
                    "type": "plotly",
                    "figure": fig,
                }
            )

        # ------------------------------------------------------------------
        # 3. Ranking / Prioridad (bar_chart – risk_priority)
        # ------------------------------------------------------------------
        elif chart_type == "bar_chart" and metric == "risk_priority":
            risk_summary = analysis.get("risk_summary", {})

            dominant = risk_summary.get("dominant_risk")
            relevant = risk_summary.get("relevant_risk")

            labels = []
            values = []

            if dominant:
                labels.append(dominant)
                values.append(2)

            if relevant and relevant != dominant:
                labels.append(relevant)
                values.append(1)

            if not labels:
                continue

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=labels,
                        y=values,
                    )
                ]
            )

            fig.update_layout(
                title="Prioridad de riesgos",
                xaxis_title="Riesgo",
                yaxis_title="Nivel de prioridad",
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
            )

            rendered_outputs.append(
                {
                    "type": "plotly",
                    "figure": fig,
                }
            )

        # ------------------------------------------------------------------
        # 4. Tabla genérica (si se necesita en el futuro)
        # ------------------------------------------------------------------
        elif chart_type == "table":
            table_data = suggestion.get("data")

            if isinstance(table_data, list):
                df = pd.DataFrame(table_data)
                rendered_outputs.append(
                    {
                        "type": "table",
                        "data": df,
                    }
                )

    return rendered_outputs
