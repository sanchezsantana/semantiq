from src.state.state import K9State


def narrative_node(state: K9State) -> K9State:
    """
    Narrative Node v0.3 — Demo-friendly tone + explicit fallback

    - Convierte analysis en narrativa clara
    - Incluye fallback honesto cuando no hay señales
    - Determinista, sin LLM
    """

    analysis = state.analysis or {}
    parts = []

    areas = analysis.get("areas_analizadas")
    window = analysis.get("signals_window")
    obs = analysis.get("observations_count")
    nm = analysis.get("near_miss_count")
    top_risk = analysis.get("top_risk")

    # Caso normal: hay señales suficientes
    if window and obs is not None and nm is not None:
        if areas:
            parts.append(
                f"El análisis se centró principalmente en el área de {', '.join(areas)}."
            )
        parts.append(f"En los {window},")
        parts.append(
            f"se registraron {obs} observaciones y {nm} eventos tipo near miss."
        )
        if top_risk:
            parts.append(
                f"El riesgo con mayor presencia durante este periodo fue {top_risk}."
            )

        state.reasoning.append(
            "NarrativeNode v0.3: narrativa generada con señales suficientes."
        )

    # Fallback explícito: no hay señales suficientes
    else:
        if areas:
            parts.append(
                f"El análisis considera el área de {', '.join(areas)},"
            )

        parts.append(
            "pero aún no se dispone de información suficiente para generar un resumen semanal completo."
        )
        parts.append(
            "A medida que se registren observaciones y señales operacionales, el sistema podrá identificar tendencias y riesgos prioritarios."
        )

        state.reasoning.append(
            "NarrativeNode v0.3: fallback narrativo por ausencia de señales."
        )

    state.answer = " ".join(parts)

    return state
