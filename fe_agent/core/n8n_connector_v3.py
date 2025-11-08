# ============================================================
#  core/n8n_connector_v3.py
#  Versión 3 - Con fallback integrado y trazabilidad cognitiva
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-29
# ============================================================

import json
import requests
from datetime import datetime
from typing import Any, Dict, Optional

from core.fallback_manager import FallbackManager


class N8NConnectorV3:
    """
    Gestiona la comunicación entre el Agente FE y el motor n8n.
    Incluye:
    - búsqueda de acciones en el diccionario operativo,
    - ejecución con manejo de errores controlado,
    - integración con el FallbackManager,
    - trazabilidad completa (logs locales).
    """

    def __init__(self,
                 diccionario_path: str = "data/FE_diccionario_operativo_integrado_v4.json",
                 default_url: str = "http://localhost:5678/webhook/",
                 timeout: int = 60,
                 log_path: str = "data/n8n_logs.json"):
        self.diccionario_path = diccionario_path
        self.default_url = default_url
        self.default_timeout = timeout
        self.log_path = log_path
        self.fb = FallbackManager()
        self.diccionario = self._load_diccionario()

    # ------------------------------------------------------------
    # UTILIDADES INTERNAS
    # ------------------------------------------------------------

    def _load_diccionario(self) -> Dict[str, Any]:
        """Carga el diccionario operativo con las acciones disponibles."""
        try:
            with open(self.diccionario_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[N8NConnectorV3] Error cargando diccionario: {e}")
            return {}

    def _log_result(self, registro: Dict[str, Any]) -> None:
        """Guarda un log local de cada ejecución (trazabilidad cognitiva)."""
        registro["timestamp"] = datetime.now().isoformat()
        try:
            logs = []
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except FileNotFoundError:
                logs = []
            logs.append(registro)
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(logs[-200:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[N8NConnectorV3] Error escribiendo log: {e}")

    def _find_action(self, accion: str) -> Optional[Dict[str, Any]]:
        """Busca una acción en el diccionario operativo."""
        try:
            if accion in self.diccionario.get("acciones", {}):
                return self.diccionario["acciones"][accion]
        except Exception:
            pass
        return None

    # ------------------------------------------------------------
    # EJECUCIÓN PRINCIPAL
    # ------------------------------------------------------------

    def execute(self, accion: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una acción del diccionario a través del motor n8n.
        Devuelve respuesta estructurada lista para Streamlit.
        """
        resultado = {"ok": False, "accion": accion, "data": None, "error": None}
        info = self._find_action(accion)

        # Acción no encontrada
        if not info:
            error_msg = f"No se encontró la acción '{accion}' en el diccionario operativo."
            fb = self.fb.handle(
                user_input=f"(interno) ejecución de '{accion}'",
                motivo=error_msg,
                tipo="n8n",
                accion=accion
            )
            resultado.update({"error": error_msg, "data": fb})
            self._log_result(resultado)
            return resultado

        # Construir URL del webhook
        endpoint = info.get("webhook_url") or info.get("webhook") or accion
        if not endpoint.startswith("http"):
            endpoint = self.default_url.rstrip("/") + f"/{endpoint.lstrip('/')}"

        try:
            response = requests.post(endpoint, json=parametros, timeout=self.default_timeout)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "json" in content_type:
                data = response.json()
            else:
                data = {"texto": response.text}

            resultado.update({"ok": True, "data": data})
            self._log_result(resultado)
            return resultado

        except Exception as e:
            error_msg = f"Error ejecutando '{accion}': {e}"
            fb = self.fb.handle(
                user_input=f"(interno) ejecución de '{accion}'",
                motivo=str(e),
                tipo="n8n",
                accion=accion,
                parametros=parametros
            )
            resultado.update({"error": error_msg, "data": fb})
            self._log_result(resultado)
            return resultado
