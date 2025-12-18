# src/data/data_manager.py

from pathlib import Path
import pandas as pd


class DataManager:
    """
    DataManager — FASE 1 (Baseline PRE lunes crítico)

    Responsabilidad única:
    - Cargar datasets sintéticos base desde disco
    - Exponerlos como DataFrames limpios
    """

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)

    # ---------- Helpers internos ----------

    def _load_csv(self, filename: str) -> pd.DataFrame:
        path = self.base_path / filename
        if not path.exists():
            raise FileNotFoundError(f"Dataset no encontrado: {path}")
        return pd.read_csv(path)

    def _load_parquet(self, filename: str) -> pd.DataFrame:
        path = self.base_path / filename
        if not path.exists():
            raise FileNotFoundError(f"Dataset no encontrado: {path}")
        return pd.read_parquet(path)

    # ---------- Datasets FASE 1 ----------

    def get_weekly_signals(self) -> pd.DataFrame:
        """
        k9_weekly_signals.parquet
        Señales semanales agregadas por riesgo
        """
        return self._load_parquet("k9_weekly_signals.parquet")

    def get_trayectorias_semanales(self) -> pd.DataFrame:
        """
        stde_trayectorias_semanales.csv
        Evolución temporal de riesgos (fuente principal de tendencias)
        """
        return self._load_csv("stde_trayectorias_semanales.csv")

    def get_observaciones(self) -> pd.DataFrame:
        """
        stde_observaciones_12s.csv
        Observaciones OPG / OCC por semana
        """
        return self._load_csv("stde_observaciones_12s.csv")

    def get_proactivo_semanal(self) -> pd.DataFrame:
        """
        stde_proactivo_semanal_v4_4.csv
        Salida semanal del modelo proactivo
        """
        return self._load_csv("stde_proactivo_semanal_v4_4.csv")
