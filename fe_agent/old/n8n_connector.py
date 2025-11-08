# n8n_connector.py
# Connector for executing actions through n8n webhooks defined in the integrated dictionary.

from __future__ import annotations
import os, json, requests
from typing import Dict, Any, Tuple

DEFAULT_DICT_PATH = os.getenv("FE_DICT_PATH", "data/FE_diccionario_operativo_integrado_v3.json")
DEFAULT_TIMEOUT = float(os.getenv("N8N_TIMEOUT", "60"))

class N8NConnector:
    def __init__(self, diccionario_path: str = DEFAULT_DICT_PATH, default_timeout: float = DEFAULT_TIMEOUT) -> None:
        with open(diccionario_path, "r", encoding="utf-8") as f:
            self.diccionario = json.load(f)
        self.default_timeout = default_timeout

    def _find_action(self, accion: str) -> Tuple[bool, str, Dict[str, Any]]:
        for scope in ("acciones_operativas","acciones_gerenciales","acciones_genericas"):
            if accion in self.diccionario.get(scope, {}):
                return True, scope, self.diccionario[scope][accion]
        return False, "", {}

    def execute(self, accion: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        ok, scope, accion_def = self._find_action(accion)
        if not ok:
            return {"ok": False, "error": f"Acción no encontrada: {accion}", "data": None}

        webhook = accion_def.get("webhook")
        if not webhook:
            return {"ok": False, "error": f"Webhook no definido para acción: {accion}", "data": None}

        try:
            r = requests.post(webhook, json=parametros or {}, timeout=self.default_timeout)
            r.raise_for_status()
            data = r.json() if r.headers.get("content-type","").startswith("application/json") else {"text": r.text}
            return {"ok": True, "error": None, "data": data, "accion": accion, "scope": scope}
        except Exception as e:
            return {"ok": False, "error": f"n8n_call_failed: {e}", "data": None, "accion": accion, "scope": scope}
