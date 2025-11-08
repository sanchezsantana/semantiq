# llm_interpreter.py
# Interpreter for mapping natural-language questions to structured actions (accion + parametros)
# Configured for Gemma 2B served via Ollama (localhost:11434).

from __future__ import annotations
import os, json, re, requests
from typing import Dict, Any, Optional, Tuple, List

DEFAULT_DICT_PATH = os.getenv("FE_DICT_PATH", "data/FE_diccionario_operativo_integrado_v3.json")
DEFAULT_PREG_PATH = os.getenv("FE_PREG_PATH", "data/FE_preguntas_respuestas.json")
DEFAULT_PROMPT_PATH = os.getenv("FE_PROMPT_PATH", "data/FE_prompt_instruccional.json")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/generate")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma:2b")

class LLMInterpreter:
    def __init__(
        self,
        diccionario_path: str = DEFAULT_DICT_PATH,
        preguntas_path: str = DEFAULT_PREG_PATH,
        prompt_instruccional_path: str = DEFAULT_PROMPT_PATH,
        llm_endpoint: str = LLM_ENDPOINT,
        llm_model: str = LLM_MODEL,
        temperature: float = 0.1,
        max_actions_in_prompt: int = 14,
        max_questions_in_prompt: int = 10,
    ) -> None:
        self.diccionario_path = diccionario_path
        self.preguntas_path = preguntas_path
        self.prompt_instruccional_path = prompt_instruccional_path
        self.llm_endpoint = llm_endpoint
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_actions_in_prompt = max_actions_in_prompt
        self.max_questions_in_prompt = max_questions_in_prompt
        self._load_assets()

    # ---------- Public API ----------
    def interpretar(self, pregunta_usuario: str) -> Dict[str, Any]:
        """
        Returns:
        {
          "accion": "<id_accion>",
          "parametros": { ... },
          "missing_params": ["fecha_inicio", ...]   # optional
        }
        """
        prompt = self._build_prompt(pregunta_usuario)
        raw = self._call_llm(prompt)
        parsed = self._safe_parse_json(raw)

        if not isinstance(parsed, dict) or "accion" not in parsed:
            return self._fallback(pregunta_usuario, reason="json_invalid_or_missing_accion", raw=raw)

        accion = parsed.get("accion")
        parametros = parsed.get("parametros", {}) or {}

        ok, _, accion_def = self._resolve_accion(accion)
        if not ok:
            return self._fallback(pregunta_usuario, reason=f"unknown_action:{accion}", raw=raw)

        missing = self._missing_params(accion_def, parametros)
        result = {"accion": accion, "parametros": parametros}
        if missing:
            result["missing_params"] = missing
        return result

    # ---------- Internals ----------
    def _load_assets(self) -> None:
        with open(self.diccionario_path, "r", encoding="utf-8") as f:
            self.diccionario = json.load(f)
        with open(self.preguntas_path, "r", encoding="utf-8") as f:
            self.preguntas = json.load(f)
        with open(self.prompt_instruccional_path, "r", encoding="utf-8") as f:
            self.prompts = json.load(f)

        self._acciones = {
            "operativas": list(self.diccionario.get("acciones_operativas", {}).keys()),
            "gerenciales": list(self.diccionario.get("acciones_gerenciales", {}).keys()),
            "genericas": list(self.diccionario.get("acciones_genericas", {}).keys()),
        }
        self._acciones_all = self._acciones["operativas"] + self._acciones["gerenciales"] + self._acciones["genericas"]
        self._preguntas_text = [p.get("pregunta") for p in self.preguntas if isinstance(p.get("pregunta"), str)]

        self._action_defs = {}
        for scope in ("acciones_operativas","acciones_gerenciales","acciones_genericas"):
            for k,v in self.diccionario.get(scope, {}).items():
                self._action_defs[k] = v

    def _resolve_accion(self, accion: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        for scope in ("acciones_operativas","acciones_gerenciales","acciones_genericas"):
            if accion in self.diccionario.get(scope, {}):
                return True, scope, self.diccionario[scope][accion]
        return False, None, None

    def _missing_params(self, accion_def: Dict[str, Any], given: Dict[str, Any]) -> List[str]:
        required = accion_def.get("input_requerido", []) or []
        return [p for p in required if given.get(p) in (None, "", [])]

    def _build_prompt(self, pregunta_usuario: str) -> str:
        acciones_sample = self._acciones_all[: self.max_actions_in_prompt]
        preguntas_sample = self._preguntas_text[: self.max_questions_in_prompt]

        rol = (
            "Eres el INTÉRPRETE SEMÁNTICO del Agente FE (Ferretería). "
            "Convierte preguntas del usuario en una INSTRUCCIÓN JSON válida para ejecución en n8n. "
            "Debes responder SOLO con un objeto JSON de una sola línea (sin texto extra). "
        )
        reglas = (
            "Reglas:\n"
            "1) 'accion' debe ser una de las acciones disponibles.\n"
            "2) 'parametros' es un objeto (puede estar vacío). Si falta información, coloca null o no incluyas el campo.\n"
            "3) NO agregues comentarios, ni markdown, ni texto fuera del JSON.\n"
        )
        disponibles = (
            f"Acciones disponibles (muestra): {acciones_sample}\n"
            f"Preguntas de referencia (muestra): {preguntas_sample}\n"
        )
        ejemplo = (
            'Ejemplo de salida JSON estricta:\n'
            '{"accion":"ventas_totales_periodo","parametros":{"fecha_inicio":"2025-01-01","fecha_fin":"2025-03-31"}}\n'
        )
        user = f'Pregunta del usuario: "{pregunta_usuario}"\n'

        prompt = f"{rol}\n{reglas}\n{disponibles}\n{ejemplo}{user}Devuelve solo el JSON:"
        return prompt

    def _call_llm(self, prompt: str) -> str:
        try:
            resp = requests.post(
                self.llm_endpoint,
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "stream": False
                },
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except Exception as e:
            return f'{{"accion":"respuesta_fallback","parametros":{{"error":"llm_call_failed","detail":"{str(e)}"}}}}'

    def _safe_parse_json(self, text: str) -> Any:
        try:
            return json.loads(text)
        except Exception:
            pass
        m = re.search(r'\{.*\}', text, flags=re.DOTALL)
        if m:
            candidate = m.group(0)
            try:
                return json.loads(candidate)
            except Exception:
                return {"accion":"respuesta_fallback","parametros":{"error":"json_parse_failed","raw":text[:4000]}}
        return {"accion":"respuesta_fallback","parametros":{"error":"no_json_returned","raw":text[:4000]}}
