from src.state.state import K9State


def analyst_node(state: K9State) -> K9State:
    """
    AnalystNode v1.1 — FASE 1 (Baseline Cognitivo PRE lunes crítico)

    Rol:
    - Consolidar análisis determinista producido por DataEngineNode
    - Implementar capacidades cognitivas FASE 1:
        1. Riesgo dominante vs relevante
        2. Evolución temporal
        3. Justificación observacional
        5. Desalineación Proactivo vs K9
        9. Umbrales cognitivos (implícitos)
    - NO generar narrativa
    - NO usar LLM
    """

    analysis = {}
    engine = state.analysis.get("engine", {})

    # ------------------------------------------------------------------
    # 1. Contexto base
    # ------------------------------------------------------------------
    if state.context_bundle:
        analysis["context_version"] = state.context_bundle.get(
            "version_contexto", "unknown"
        )
        analysis["areas_analizadas"] = state.context_bundle.get(
            "areas_operacionales", []
        )

    # ------------------------------------------------------------------
    # 2. Periodo analizado
    # ------------------------------------------------------------------
    analysis["period"] = engine.get("period", {})

    # ------------------------------------------------------------------
    # 3. Evolución temporal por riesgo (Capacidad 2)
    # ------------------------------------------------------------------
    risk_trajectories = {}
    engine_trends = engine.get("risk_trends", {})

    for risk, data in engine_trends.items():
        trend_direction = data.get("trend_direction")

        if trend_direction == "up":
            temporal_state = "degrading"
        elif trend_direction == "down":
            temporal_state = "improving"
        else:
            temporal_state = "stable"

        risk_trajectories[risk] = {
            "weekly_values": data.get("weekly_values", []),
            "trend_direction": trend_direction,
            "temporal_state": temporal_state,
        }

    analysis["risk_trajectories"] = risk_trajectories

    # ------------------------------------------------------------------
    # 4. Observaciones operacionales (Capacidad 3)
    # FASE 1 + FASE 2 compatible
    # ------------------------------------------------------------------
    observations_summary = {}

    # Observaciones globales (FASE 1)
    obs_engine = engine.get("observations", {})
    obs_by_type = obs_engine.get("by_type", {})

    global_opg_count = (
        obs_by_type.get("OPG", {}).get("count", 0)
        if isinstance(obs_by_type.get("OPG"), dict)
        else 0
    )
    global_occ_count = (
        obs_by_type.get("OCC", {}).get("count", 0)
        if isinstance(obs_by_type.get("OCC"), dict)
        else 0
    )

    # Enriquecimiento OCC por riesgo (FASE 2)
    risk_enrichment = getattr(state, "risk_enrichment", None)

    for risk in risk_trajectories.keys():

        # Defaults FASE 1
        opg_count = global_opg_count
        occ_count = global_occ_count
        support_level = "none"

        # FASE 2: OCC asociados a riesgo
        if risk_enrichment and "by_risk" in risk_enrichment:
            occ_events = (
                risk_enrichment["by_risk"]
                .get(risk, {})
                .get("occ_events", [])
            )
            occ_count = len(occ_events)

            if occ_count > 0:
                critical_controls = [
                    e for e in occ_events if e.get("is_control_critico")
                ]   

                if len(critical_controls) > 0:
                    support_level = "strong"
                else:
                    support_level = "moderate"
            else:
                support_level = "none"

        observations_summary[risk] = {
            "opg_count": opg_count,
            "occ_count": occ_count,
            "support_level": support_level,
        }

    analysis["observations_summary"] = observations_summary

    # ------------------------------------------------------------------
    # 4.b Evidencia operacional por riesgo (Capacidad 10 — FASE 2)
    # ------------------------------------------------------------------
    operational_evidence = {
        "has_operational_support": False,
        "supported_risks": [],
        "evidence_by_risk": {},
    }

    for risk, obs in observations_summary.items():
        occ_count = obs.get("occ_count", 0)
        support_level = obs.get("support_level", "none")

        if occ_count > 0 and support_level != "none":
            operational_evidence["has_operational_support"] = True
            operational_evidence["supported_risks"].append(risk)

            # ¿Hay controles críticos involucrados?
            has_critical = False
            if risk_enrichment and "by_risk" in risk_enrichment:
                occ_events = (
                    risk_enrichment["by_risk"]
                    .get(risk, {})
                    .get("occ_events", [])
                )
                has_critical = any(
                    e.get("is_control_critico") for e in occ_events
                )

            operational_evidence["evidence_by_risk"][risk] = {
                "occ_count": occ_count,
                "support_level": support_level,
                "has_critical_control_failures": has_critical,
            }

    analysis["operational_evidence"] = operational_evidence


    # ------------------------------------------------------------------
    # 5. Riesgo dominante vs relevante (Capacidad 1)
    # ------------------------------------------------------------------
    weekly_signals = engine.get("weekly_signals", {})

    dominant_risk = None
    max_criticidad = -1

    for risk, data in weekly_signals.items():
        criticidad = data.get("avg_criticidad")
        if criticidad is not None and criticidad > max_criticidad:
            max_criticidad = criticidad
            dominant_risk = risk

    relevant_risk = None
    for risk, traj in risk_trajectories.items():
        if (
            risk != dominant_risk
            and traj.get("temporal_state") == "degrading"
        ):
            relevant_risk = risk
            break

    analysis["risk_summary"] = {
        "dominant_risk": dominant_risk,
        "relevant_risk": relevant_risk,
    }

    # ------------------------------------------------------------------
    # 6. Proactivo vs K9 (Capacidad 5)
    # ------------------------------------------------------------------
    proactive_comparison = {}
    proactivo_engine = engine.get("proactivo_vs_k9", {})

    for risk, data in proactivo_engine.items():
        avg_rank_k9 = data.get("avg_rank_k9")
        avg_rank_proactivo = data.get("avg_rank_proactivo")
        rank_delta = data.get("rank_delta")

        if avg_rank_k9 is not None and avg_rank_proactivo is not None:
            if rank_delta is not None and rank_delta > 1:
                alignment_status = "underestimated_by_proactive"
            elif rank_delta is not None and rank_delta < -1:
                alignment_status = "overestimated_by_proactive"
            else:
                alignment_status = "aligned"
        else:
            alignment_status = "inconclusive"

        proactive_comparison[risk] = {
            "avg_rank_k9": avg_rank_k9,
            "avg_rank_proactivo": avg_rank_proactivo,
            "rank_delta": rank_delta,
            "alignment_status": alignment_status,
        }

    analysis["proactive_comparison"] = proactive_comparison

    # ------------------------------------------------------------------
    # 7. Umbrales cognitivos implícitos (Capacidad 9)
    # ------------------------------------------------------------------
    thresholds = {}
    threshold_definition = {
        "requires_degrading_trend": True,
        "top3_ratio_min": 0.5,
    }

    for risk, traj in risk_trajectories.items():
        signal = weekly_signals.get(risk, {})
        top3_ratio = signal.get("top3_ratio", 0)

        is_approaching = (
            traj.get("temporal_state") == "degrading"
            and top3_ratio >= threshold_definition["top3_ratio_min"]
        )

        thresholds[risk] = {
            "threshold_state": (
                "approaching_threshold"
                if is_approaching
                else "below_threshold"
            ),
            "top3_ratio": top3_ratio,
            "temporal_state": traj.get("temporal_state"),
        }

    analysis["thresholds"] = {
        "definition": threshold_definition,
        "by_risk": thresholds,
    }

    # ------------------------------------------------------------------
    # 8. Persistencia final
    # ------------------------------------------------------------------
    state.analysis = analysis

    state.reasoning.append(
        "AnalystNode v1.1: análisis cognitivo FASE 1 consolidado desde DataEngine."
    )

    return state
