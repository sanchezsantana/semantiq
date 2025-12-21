# src/nodes/data_engine_node.py

# src/nodes/data_engine_node.py

from typing import Dict, List
from src.data.data_manager import DataManager
from src.state.state import K9State


def _trend_direction(values: List[float]) -> str:
    """
    Calcula dirección de tendencia simple.
    - up: último > primero
    - down: último < primero
    - flat: igual
    """
    if not values or len(values) < 2:
        return "flat"
    if values[-1] > values[0]:
        return "up"
    if values[-1] < values[0]:
        return "down"
    return "flat"


def data_engine_node(state: K9State) -> K9State:
    """
    DataEngineNode — FASE 1 (Baseline PRE lunes crítico)

    Bloques incluidos:
    - Bloque 1: Periodo + Trayectorias
    - Bloque 2: Señales semanales

    Rol:
    - Transformar data sintética base en hechos analíticos deterministas
    - NO emitir juicios cognitivos
    - NO generar narrativa
    """

    dm = DataManager("data/synthetic")

    # =====================================================
    # Bloque 1 — Periodo + Trayectorias
    # =====================================================

    df_tray = dm.get_trayectorias_semanales()

    weeks = sorted(df_tray["semana"].unique().tolist())

    engine_analysis: Dict = {
        "period": {
            "min_week": weeks[0],
            "max_week": weeks[-1],
            "weeks": weeks,
        },
        "risk_trends": {},
    }

    risk_columns = [
        col for col in df_tray.columns
        if col.startswith("criticidad_")
        and col.endswith("_media")
        and col != "criticidad_global_media"
    ]

    for col in risk_columns:
        riesgo_id = col.replace("criticidad_", "").replace("_media", "")
        values = (
            df_tray
            .sort_values("semana")[col]
            .tolist()
        )

        engine_analysis["risk_trends"][riesgo_id] = {
            "weekly_values": values,
            "trend_direction": _trend_direction(values),
        }

    # =====================================================
    # Bloque 2 — Señales semanales
    # =====================================================

    df_signals = dm.get_weekly_signals()

    engine_analysis["weekly_signals"] = {}

    for riesgo_id in engine_analysis["risk_trends"].keys():
        df_risk = df_signals[df_signals["riesgo_id"] == riesgo_id]

        if df_risk.empty:
            continue

        avg_criticidad = df_risk["criticidad_media"].mean()
        avg_rank = df_risk["rank_pos"].mean()
        top3_weeks = int(df_risk["is_top3"].sum())
        total_weeks = df_risk["semana"].nunique()

        engine_analysis["weekly_signals"][riesgo_id] = {
            "avg_criticidad": float(avg_criticidad),
            "avg_rank_pos": float(avg_rank),
            "top3_weeks": top3_weeks,
            "is_top3_ratio": (
                top3_weeks / total_weeks if total_weeks > 0 else 0.0
            ),
        }
    # =====================================================
    # Bloque 3 — Observaciones operacionales (OPG / OCC)
    # FASE 1 — vista unificada
    # =====================================================

    df_obs = dm.get_observaciones_all()

    engine_analysis["observations"] = {
        "summary": {
            "total": int(len(df_obs)),
            "by_type": {}
        },
        "weekly": {
            "OPG": {},
            "OCC": {}
        },
        "sources": {
            "baseline": "stde_observaciones.csv",
            "stde": "stde_observaciones_12s.csv"
        }
    }

    for obs_type in ["OPG", "OCC"]:
        df_t = df_obs[df_obs["tipo_observacion"] == obs_type]

        engine_analysis["observations"]["summary"]["by_type"][obs_type] = int(len(df_t))

        weekly = (
            df_t.groupby("semana")
            .size()
            .to_dict()
        )

        engine_analysis["observations"]["weekly"][obs_type] = {
            int(k): int(v) for k, v in weekly.items()
        }
        

    
    
    # =====================================================
    # Bloque 4 — Proactivo vs K9 (Baseline PRE lunes crítico)
    # =====================================================

    df_proactivo = dm.get_proactivo_semanal()

    engine_analysis["proactivo"] = {}

    required_cols = {"semana_id", "riesgo_id", "score_proactivo", "rank_proactivo"}
    missing = required_cols - set(df_proactivo.columns)
    if missing:
        raise KeyError(
            f"stde_proactivo_semanal_v4_4.csv missing columns: {missing}"
        )

    # Ranking promedio y score promedio por riesgo (modelo proactivo)
    for riesgo_id, df_r in df_proactivo.groupby("riesgo_id"):
        engine_analysis["proactivo"][riesgo_id] = {
            "avg_score_proactivo": float(df_r["score_proactivo"].mean()),
            "avg_rank_proactivo": float(df_r["rank_proactivo"].mean()),
            "weeks_considered": int(df_r["semana_id"].nunique()),
        }

    # Comparación K9 vs Proactivo (si existe señal K9)
    if "weekly_signals" in engine_analysis:
        engine_analysis["proactivo_vs_k9"] = {}

        for riesgo_id, p_data in engine_analysis["proactivo"].items():
            k9_data = engine_analysis["weekly_signals"].get(riesgo_id)

            if not k9_data:
                continue

            engine_analysis["proactivo_vs_k9"][riesgo_id] = {
                "avg_rank_k9": float(k9_data["avg_rank_pos"]),
                "avg_rank_proactivo": float(p_data["avg_rank_proactivo"]),
                "rank_delta": float(
                    p_data["avg_rank_proactivo"] - k9_data["avg_rank_pos"]
                ),
            }



    # =====================================================
    # Persistencia FINAL del engine
    # =====================================================

    state.analysis = state.analysis or {}
    state.analysis["engine"] = engine_analysis

    state.reasoning.append(
    "DataEngineNode FASE 1: análisis determinista completo ejecutado "
    "(trayectorias, señales, observaciones y comparación Proactivo vs K9)."
    )

    return state

