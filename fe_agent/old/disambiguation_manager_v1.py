# ============================================================
#  core/disambiguation_manager_v1.py
#  Modo de desambiguación asistida por LLM (historial + hipótesis)
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-30
# ============================================================

from __future__ import annotations
import json
import requests
from typing import Dict, Any, Optional, List


class DisambiguationManagerV1:
    """
    Invoca al LLM en 'modo aclaración' cuando:
    - la entrada es ambigua/fragmentaria/contradictoria,
    - la intención parece fuera del alcance del agente FE.

    Retorna un JSON estructurado:
    {
      "status": "clarify" | "in_scope" | "out_of_scope",
      "reason": "texto breve",
      "clarification_question": "pregunta empática para avanzar",
      "rephrased_question": "reformulación tentativa de la intención del usuario",
      "candidate_intents": [
         {"accion": "consultar_total_ventas", "parametros": {...}, "confidence": 0.82}
      ]
    }
    """

    def __init__(self,
                 llm_url: str = "http://localhost:11434/api/generate",
                 model: str = "gemma:2b",
                 scope_domains: Optional[List[str]] = None,
                 temperature: float = 0.2,
                 max_tokens: int = 800):
        self.llm_url = llm_url
        self.model = model
        self.scope_domains = scope_domains or [
            "ventas ferretería", "compras ferretería", "margen", "productos", "clientes", "proveedores", "stock"
        ]
        self.temperature = temperature
        self.max_tokens = max_tokens

    # ------------------------------------------------------------
    #  PÚBLICO
    # ------------------------------------------------------------
    def clarify(self, user_input: str, llm_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye un prompt de aclaración y devuelve un dict con la estructura definida.
        """
        prompt = self._build_prompt(user_input, llm_context)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature}
        }

        try:
            resp = requests.post(self.llm_url, json=payload, timeout=60)
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            # Intentar parsear JSON directo
            data = self._safe_parse_json(text)
            if not isinstance(data, dict):
                # fallback mínimo
                data = {
                    "status": "clarify",
                    "reason": "Respuesta no JSON del modelo",
                    "clarification_question": "¿Podrías precisar a qué período, producto o cliente te refieres?",
                    "rephrased_question": None,
                    "candidate_intents": []
                }
            return self._sanitize(data)
        except Exception as e:
            return {
                "status": "clarify",
                "reason": f"Error al invocar LLM: {e}",
                "clarification_question": "No me quedó del todo claro el objetivo. ¿Puedes especificar el período o el indicador que quieres analizar?",
                "rephrased_question": None,
                "candidate_intents": []
            }

    # ------------------------------------------------------------
    #  PRIVADO
    # ------------------------------------------------------------
    def _build_prompt(self, user_input: str, ctx: Dict[str, Any]) -> str:
        # Historial compacto
        hist = ctx.get("historial_reciente", [])
        hist_lines = []
        for h in hist:
            q = h.get("pregunta", "")
            r = (h.get("respuesta", "") if isinstance(h.get("respuesta"), str) else "[respuesta estructurada]")
            hist_lines.append(f"- Usuario: {q}\n  Agente: {r}")

        scope_str = ", ".join(self.scope_domains)

        # Instrucciones estrictas para respuesta JSON
        return f"""
Eres un analista cognitivo experto en desambiguar intenciones del usuario para un agente de ferretería (ventas, compras, margen, productos, clientes, proveedores, stock).
Tu objetivo: analizar la entrada actual y el historial reciente para:
1) proponer una pregunta de aclaración breve y empática,
2) sugerir una reformulación tentativa de la intención,
3) listar de 0 a 3 hipótesis operativas (accion + parametros) con un score de confianza en [0.0, 1.0],
4) clasificar el caso como "in_scope", "clarify" o "out_of_scope".
   - "in_scope": puedes mapear razonablemente a una acción del dominio.
   - "clarify": falta un dato crucial (periodo, entidad, métrica) para elegir acción.
   - "out_of_scope": la intención excede el alcance del agente (dominios esperados: {scope_str}).

Responde SOLO un JSON con esta forma exacta:
{{
  "status": "clarify" | "in_scope" | "out_of_scope",
  "reason": "string breve",
  "clarification_question": "string o null",
  "rephrased_question": "string o null",
  "candidate_intents": [
     {{"accion":"...", "parametros":{{}}, "confidence":0.0}}
  ]
}}

Reglas de estilo:
- Sé empático y conciso.
- Si "out_of_scope", ofrece una alternativa breve (p. ej., reformular dentro del dominio) en "clarification_question".
- No inventes datos ni ejecutes cálculos.

Historial reciente:
{chr(10).join(hist_lines)}

Entrada del usuario (actual):
\"\"\"{user_input}\"\"\"
"""

    def _safe_parse_json(self, text: str) -> Any:
        try:
            return json.loads(text)
        except Exception:
            # Intento de extracción tosca si viene envuelto
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                fragment = text[start:end+1]
                try:
                    return json.loads(fragment)
                except Exception:
                    return None
            return None

    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data.setdefault("status", "clarify")
        data.setdefault("reason", "")
        data.setdefault("clarification_question", None)
        data.setdefault("rephrased_question", None)
        ci = data.get("candidate_intents", [])
        if not isinstance(ci, list):
            data["candidate_intents"] = []
        else:
            # Normalizar campos de cada candidato
            norm = []
            for c in ci:
                if not isinstance(c, dict):
                    continue
                norm.append({
                    "accion": c.get("accion"),
                    "parametros": c.get("parametros") or {},
                    "confidence": float(c.get("confidence") or 0.0)
                })
            data["candidate_intents"] = norm[:3]
        return data
