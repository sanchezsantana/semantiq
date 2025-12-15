from src.state.state import K9State


def analyst_node(state: K9State) -> K9State:
    """
    AnalystNode v0.2

    Rol:
    - Leer contexto estructural (context_bundle)
    - Enriquecer análisis usando signals (STDE)
    - NO generar respuesta final
    - NO usar modelos
    """

    analysis = {}

    # --- Análisis base desde contexto ---
    if state.context_bundle:
        analysis["context_version"] = state.context_bundle.get(
            "version_contexto", "unknown"
        )
        analysis["areas_analizadas"] = state.context_bundle.get(
            "areas_operacionales", []
        )
    else:
        analysis["warning"] = "No context_bundle available for analysis"

    # --- Enriquecimiento usando signals (si existen) ---
    if state.signals:
        analysis["signals_window"] = (
            state.signals.get("window")
            or state.signals.get("signals_window")
        )
        analysis["observations_count"] = state.signals.get(
            "observations_count", 0
        )
        analysis["near_miss_count"] = state.signals.get(
            "near_miss_count", 0
        )
        analysis["top_risk"] = state.signals.get("top_risk")

        state.reasoning.append(
            "AnalystNode v0.2: análisis enriquecido usando signals (STDE)."
        )
    else:
        state.reasoning.append(
            "AnalystNode v0.2: análisis estructural sin signals."
        )

    # --- Persistencia ---
    state.analysis = analysis

    return state
