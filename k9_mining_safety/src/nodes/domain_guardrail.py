from src.state.state import K9State

def domain_guardrail(state: K9State) -> K9State:
    """
    Reglas del dominio K9 Mining Safety.
    Verifica si la intención es del dominio minería/seguridad operacional.
    Si no pertenece, activa demo_mode y marca out_of_domain.
    """

    MINING_INTENTS = {
        "greeting",
        "proactive_model",
        "riesgos",
        "risk_caida_altura",
        "risk_caida_objetos",
        "risk_contacto_energia",
        "mining_general",
        "predictor",
        "analyst",
        "consulta_riesgo",
        "consulta_eventos",
        "consulta_area",
        "consulta_bowtie",
        "bowtie",
    }

    # --------------------------
    # 1) Si el intent está claramente dentro del dominio minería
    # --------------------------
    if state.intent in MINING_INTENTS:
        state.reasoning.append(
            f"Domain Guardrail: intent '{state.intent}' pertenece al dominio minería."
        )
        return state

    # --------------------------
    # 2) Caso especial: general_question
    # Solo pertenece al dominio si contiene palabras de minería
    # --------------------------
    mining_keywords = [
        "mina", "rajo", "faena", "escondida", "camión", "pala",
        "alturas", "planta", "concentradora", "chancado", "taller",
        "mantención", "lixiviación", "scoop",
        "área", "áreas", "operacional", "operacionales"
    ]

    if state.intent == "general_question":
        if any(k in state.user_query.lower() for k in mining_keywords):
            state.reasoning.append(
                f"Domain Guardrail: 'general_question' contiene señales de minería, se acepta."
            )
            return state

        # No contiene señales → fuera de dominio
        state.intent = "out_of_domain"
        state.demo_mode = True
        state.reasoning.append(
            "Domain Guardrail: 'general_question' sin señales de minería → fuera de dominio (demo_mode=True)."
        )
        return state

    # --------------------------
    # 3) Todo lo demás → fuera de dominio
    # --------------------------
    state.intent = "out_of_domain"
    state.demo_mode = True
    state.reasoning.append(
        f"Domain Guardrail: intent '{state.intent}' fuera de dominio → demo_mode=True."
    )
    return state
