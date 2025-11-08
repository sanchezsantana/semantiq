# ============================================================
#  core/disambiguation_manager_v2.py
#  LLM-Assisted Disambiguation (con hipótesis locales)
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-31
# ============================================================

import json
import requests
from typing import Dict, Any, List, Optional


class DisambiguationManagerV2:
    """
    Invoca al LLM para clarificar preguntas ambiguas o fuera de dominio.
    Propone contra-preguntas empáticas e hipótesis clasificadas.
    """

    def __init__(self,
                 llm_url: str = "http://localhost:11434/api/generate",
                 model: str = "gemma:2b",
                 temperature: float = 0.3):
        self.llm_url = llm_url
        self.model = model
        self.temperature = temperature
        self.scope_domains = [
            "ventas", "compras", "margen", "productos", "clientes",
            "proveedores", "stock", "rotación", "categorías"
        ]

    # ------------------------------------------------------------
    def clarify(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(user_input, context)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature}
        }

        try:
            res = requests.post(self.llm_url, json=payload, timeout=60)
            res.raise_for_status()
            raw = res.json().get("response", "")
            parsed = self._safe_json(raw)
            return self._normalize(parsed)
        except Exception as e:
            return {
                "status": "clarify",
                "reason": f"Error al procesar aclaración: {e}",
                "clarification_question": "¿Podrías precisar si te refieres a ventas, compras o margen?",
                "candidate_intents": []
            }

    # ------------------------------------------------------------
    def _build_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        hist = context.get("historial_reciente", [])
        hist_text = "\n".join(
            [f"- Usuario: {h.get('pregunta','')}\n  Agente: {h.get('respuesta','')}" for h in hist]
        )
        domains = ", ".join(self.scope_domains)
        return f"""
Eres un analista cognitivo que ayuda a clarificar intenciones en un agente de ferretería.

Tu tarea:
1. Analiza la pregunta actual y el historial.
2. Si está fuera del dominio ({domains}), marca "out_of_scope".
3. Si requiere precisión, genera una pregunta de aclaración breve y empática.
4. Propón hasta 3 hipótesis con su acción y nivel de confianza.

También puedes usar:
- "ui_repeat_last", "ui_show_chart", "ui_change_chart_type"
- "ui_export_csv", "ctx_set_period", "ctx_set_visual_pref"
- "confirm_previous"

Formato de salida JSON:
{{
  "status": "clarify" | "in_scope" | "out_of_scope",
  "reason": "string breve",
  "clarification_question": "string o null",
  "rephrased_question": "string o null",
  "candidate_intents": [
    {{"accion": "string", "parametros": {{}}, "confidence": 0.0}}
  ]
}}

Historial:
{hist_text}

Pregunta actual:
\"\"\"{user_input}\"\"\"
"""

    def _safe_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end != -1:
                frag = text[start:end+1]
                try:
                    return json.loads(frag)
                except Exception:
                    return {}
            return {}

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            data = {}
        data.setdefault("status", "clarify")
        data.setdefault("reason", "")
        data.setdefault("clarification_question", None)
        data.setdefault("rephrased_question", None)
        data.setdefault("candidate_intents", [])
        for c in data["candidate_intents"]:
            c.setdefault("confidence", 0.0)
            c["confidence"] = float(c["confidence"])
        return data
