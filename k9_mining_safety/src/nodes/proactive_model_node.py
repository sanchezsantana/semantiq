from typing import Any
from src.state.state import K9State

def proactive_model_node(state: K9State) -> K9State:
    state.reasoning.append("Proactive Model Node: explicando el Modelo Proactivo.")

    definicion = state.context.get("modelo_proactivo_definicion", "")
    riesgos_top = state.context.get("top_riesgos_escondida", [])
    tipos_eventos = state.context.get("tipos_eventos", {})

    respuesta = (
        f"Modelo Proactivo — Explicación General\n\n"
        f"{definicion}\n\n"
        f"• Riesgos priorizados actualmente: {', '.join(riesgos_top)}\n"
        f"• Tipos de eventos analizados: {', '.join(tipos_eventos.keys())}\n\n"
        f"El Modelo Proactivo se utiliza para anticipar tendencias de riesgo "
        f"en ventanas de corto plazo (generalmente 4 a 7 semanas) para apoyar "
        f"la toma de decisiones operacionales."
    )

    state.answer = respuesta
    return state
