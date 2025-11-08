# ============================================================
#  core/n8n_connector_v2.py
#  Versión 2 - Conector operativo con soporte para v4
# ============================================================

import os
import json
import requests
from typing import Any, Dict, Tuple

# Ruta por defecto al diccionario operativo v4
DEFAULT_DICT_PATH = os.getenv("FE_DICT_PATH", "data/FE_diccionario_operativo_integrado_v4.json")
DEFAULT_TIMEOUT = float(os.getenv("N8N_TIMEOUT", "20.0"))


class N8NConnector:
    """
    Conector entre el Agente FE y los flujos de n8n.
    Usa el diccionario operativo v4 para determinar la URL
    y metadatos asociados a cada acción.
    """

    def __init__(self, diccionario_path: str = DEFAULT_DICT_PATH, default_timeout: float = DEFAULT_TIMEOUT) -> None:
        try:
            with open(diccionario_path, "r", encoding="utf-8") as f:
                contenido = json.load(f)
                self.diccionario = contenido.get("contenido", contenido)
        except Exception as e:
            print(f"[ERROR] No se pudo cargar el diccionario operativo: {e}")
            self.diccionario = {}
        self.default_timeout = default_timeout

    # ------------------------------------------------------------
    # Buscar acción en los tres niveles del diccionario
    # ------------------------------------------------------------
    def _find_action(self, accion: str) -> Tuple[bool, str, Dict[str, Any]]:
        accion_norm = accion.lower().strip()
        for scope in ("acciones_operativas", "acciones_gerenciales", "acciones_genericas"):
            acciones = self.diccionario.get(scope, [])
            if isinstance(acciones, list):
                for a in acciones:
                    if a.get("id_accion", "").lower() == accion_norm:
                        return True, scope, a
        return False, "", {}

    # ------------------------------------------------------------
    # Ejecutar acción vía flujo n8n
    # ------------------------------------------------------------
    def execute(self, accion: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        found, scope, info = self._find_action(accion)

        if not found:
            return {
                "ok": False,
                "accion": accion,
                "error": f"No se encontró la acción '{accion}' en el diccionario operativo.",
                "data": None
            }

        webhook_url = info.get("webhook_url") or info.get("endpoint") or ""
        if not webhook_url:
            return {
                "ok": False,
                "accion": accion,
                "error": f"La acción '{accion}' no tiene una URL configurada.",
                "data": None
            }

        try:
            response = requests.post(webhook_url, json=parametros, timeout=self.default_timeout)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                data = response.json()
            else:
                data = {"texto": response.text}

            return {"ok": True, "accion": accion, "scope": scope, "data": data}

        except requests.Timeout:
            return {"ok": False, "accion": accion, "error": "Tiempo de espera agotado al conectar con n8n."}
        except Exception as e:
            return {"ok": False, "accion": accion, "error": f"Error inesperado: {str(e)}"}
