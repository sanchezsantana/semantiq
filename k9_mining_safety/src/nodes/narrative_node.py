from src.state.state import K9State


def narrative_node(state: K9State) -> K9State:
    """
    NarrativeNode v0.7 — Capa de traducción cognitiva (sin LLM)

    Rol:
    - Traducir analysis estructurado en respuesta clara y defendible
    - Distinguir entre diagnóstico y razonamiento precautorio (contrafactual)
    - NO razonar (solo traduce hechos existentes en analysis)
    - NO recalibrar
    - NO declarar eventos
    - Preparado para futura integración de LLM (traductor entrada/salida)
    """

    analysis = state.analysis or {}
    user_query = (state.user_query or "").lower()

    # ==============================================================================================
    # 0.A Override por INTENT explícito (fuente primaria)
    # ==============================================================================================
    if state.intent == "proactive_model_contrafactual":
        is_contrafactual = True
    else:
        is_contrafactual = False

    # ==============================================================================================
    # 0. Detección de modo contrafactual / precautorio (sin LLM)
    # ==============================================================================================
    contrafactual_triggers = [
        "si el modelo se equivoca",
        "si el modelo falla",
        "en caso de error",
        "si se equivoca",
        "si falla",
        "qué pasaría si",
        "deberían preocupar",
    ]
    if not is_contrafactual:
        is_contrafactual = any(t in user_query for t in contrafactual_triggers)


    # ==============================================================================================
    # 1. FASE 2 temprana — Proactivo vs K9 (diagnóstico o precautorio)
    # ==============================================================================================
    proactive = analysis.get("proactive_explanation")

    if proactive:
        alignment_status = proactive.get("alignment_status")
        explained_risks = proactive.get("explained_risks", [])  # típicamente R01/R02

        # ------------------------------------------------------------------
        # 1.A Modo CONTRAFACTUAL / PRECAUTORIO
        # ------------------------------------------------------------------
        if is_contrafactual:
            risk_summary = analysis.get("risk_summary", {})
            dominant = risk_summary.get("dominant_risk")
            relevant = risk_summary.get("relevant_risk")

            operational_evidence = analysis.get("operational_evidence", {})
            evidence_by_risk = operational_evidence.get("evidence_by_risk", {})

            # Universo permitido: riesgos explicados por el contraste
            # + (dominant/relevant) por seguridad
            allowed = set(explained_risks)
            if dominant:
                allowed.add(dominant)
            if relevant:
                allowed.add(relevant)

            # Candidatos: dentro del universo permitido + con soporte operacional
            candidates = []
            for risk in allowed:
                ev = evidence_by_risk.get(risk, {})
                occ_count = ev.get("occ_count", 0)
                has_critical = ev.get("has_critical_control_failures", False)

                if occ_count > 0:
                    candidates.append(
                        {
                            "risk": risk,
                            "occ_count": occ_count,
                            "has_critical_control_failures": has_critical,
                        }
                    )

            # Priorización: primero los que tienen fallas de control crítico,
            # luego por cantidad de OCC
            candidates.sort(
                key=lambda x: (x["has_critical_control_failures"], x["occ_count"]),
                reverse=True,
            )

            if candidates:
                risks_list = [c["risk"] for c in candidates]

                # Texto base
                state.answer = (
                    "Aunque actualmente no se observa una desalineación explícita entre "
                    "el modelo proactivo y el análisis K9, en un escenario contrafactual "
                    "donde el modelo proactivo subestima riesgos, los que deberían recibir "
                    f"mayor atención preventiva son: {', '.join(risks_list)}."
                )

                # Justificación (solo si aplica)
                if any(c["has_critical_control_failures"] for c in candidates):
                    state.answer += (
                        " Esta priorización se refuerza por la presencia de condiciones "
                        "asociadas a controles críticos en evidencia operacional reciente."
                    )
                else:
                    state.answer += (
                        " Esta priorización se basa en la evidencia operacional reciente "
                        "disponible, sin implicar la ocurrencia de un evento crítico."
                    )
            else:
                state.answer = (
                    "Actualmente, no se dispone de evidencia operacional suficiente dentro "
                    "de los riesgos evaluados para recomendar una alerta preventiva adicional "
                    "bajo un escenario contrafactual de error del modelo proactivo."
                )

            state.reasoning.append(
                "NarrativeNode v0.7: respuesta contrafactual precautoria generada "
                "restringida a riesgos explicados (dominante/relevante + contraste proactivo)."
            )
            return state

        # ------------------------------------------------------------------
        # 1.B Modo DIAGNÓSTICO (alineación real)
        # ------------------------------------------------------------------
        if alignment_status == "aligned":
            base_answer = (
                "No se observa una desalineación relevante entre el modelo proactivo "
                "y el análisis K9 para los riesgos actuales."
            )
        elif alignment_status == "underestimated":
            base_answer = (
                "El análisis K9 identifica una posible subestimación de al menos uno "
                "de los riesgos por parte del modelo proactivo."
            )
        elif alignment_status == "overestimated":
            base_answer = (
                "El modelo proactivo asigna una mayor prioridad a algunos riesgos "
                "respecto a lo observado en el análisis K9."
            )
        else:
            base_answer = (
                "No se dispone de información suficiente para establecer con claridad "
                "la alineación entre el modelo proactivo y el análisis K9."
            )

        if explained_risks:
            base_answer += (
                " Los riesgos evaluados en este contraste fueron: "
                f"{', '.join(explained_risks)}."
            )

        state.answer = base_answer
        state.reasoning.append(
            "NarrativeNode v0.7: respuesta diagnóstica generada desde proactive_explanation."
        )
        return state

    # ==============================================================================================
    # 2. FASE 1 — Riesgo dominante vs relevante + evidencia operacional
    # ==============================================================================================
    risk_summary = analysis.get("risk_summary")

    if risk_summary:
        dominant = risk_summary.get("dominant_risk")
        relevant = risk_summary.get("relevant_risk")

        base_answer = (
            f"Actualmente, el riesgo dominante es {dominant}, "
            f"manteniéndose en un nivel elevado de forma sostenida. "
            f"Por otro lado, el riesgo que más preocupa por su evolución "
            f"es {relevant}, ya que muestra una tendencia creciente "
            f"que requiere atención preventiva."
        )

        operational_evidence = analysis.get("operational_evidence", {})
        if operational_evidence.get("has_operational_support"):
            supported = operational_evidence.get("supported_risks", [])
            if supported:
                base_answer += (
                    " Además, se observa evidencia operacional reciente "
                    "que respalda el comportamiento de los riesgos "
                    f"{', '.join(supported)}, a partir de condiciones "
                    "críticas detectadas en terreno."
                )

        state.answer = base_answer
        state.reasoning.append(
            "NarrativeNode v0.7: narrativa FASE 1 generada desde risk_summary con evidencia."
        )
        return state

    # ==============================================================================================
    # 3. Fallback honesto
    # ==============================================================================================
    areas = analysis.get("areas_analizadas")

    if areas:
        state.answer = (
            f"El análisis considera las áreas de {', '.join(areas)}, "
            "pero actualmente no se dispone de información suficiente "
            "para generar una interpretación concluyente."
        )
    else:
        state.answer = (
            "Actualmente no se dispone de información suficiente "
            "para generar una interpretación confiable."
        )

    state.reasoning.append(
        "NarrativeNode v0.7: fallback narrativo por ausencia de análisis suficiente."
    )
    return state
