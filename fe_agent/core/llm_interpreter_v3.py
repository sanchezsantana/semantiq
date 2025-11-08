# ============================================================
#  llm_interpreter_v3.py
#  Versión mejorada con Finetuning Simulado (FT-sim) y
#  alineación total con FE_prompt_instruccional_v2.json
# ============================================================

import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional


class LLMInterpreterV3:
    """
    Interprete semántico del agente FE.
    Integra contexto, memoria y plantillas de prompt desde el archivo FE_prompt_instruccional_v2.json.
    Compatible con Gemma 2B/3B (vía Ollama o endpoint local).
    """

    def __init__(self,
                 llm_url: str = "http://localhost:11434/api/generate",
                 model: str = "gemma:2b",
                 prompt_file: str = "FE_prompt_instruccional_v2.json"):
        self.llm_url = llm_url
        self.model = model
        self.prompt_file = prompt_file
        self.prompt_data = self._load_prompt_file()
        self.session_history = []

    # ------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------

    def _load_prompt_file(self) -> Dict[str, Any]:
        """Carga el archivo JSON que define el comportamiento del intérprete"""
        try:
            with open(self.prompt_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Error al cargar el archivo de prompt: {e}")

    def _load_examples(self, limit: int = 5) -> str:
        """Selecciona ejemplos representativos para el FT-simulado"""
        ejemplos = self.prompt_data.get("ejemplos", [])[:limit]
        return json.dumps(ejemplos, indent=2, ensure_ascii=False)

    def _get_context_summary(self, context: Optional[Dict[str, Any]]) -> str:
        """Crea un bloque de contexto con memoria y estado actual"""
        if not context:
            return "Sin contexto previo disponible."
        resumen = {
            "ultima_accion": context.get("ultima_accion", "N/A"),
            "ultima_respuesta": context.get("ultima_respuesta", "N/A"),
            "preferencia_visual": context.get("preferencia_visual", "No definida"),
            "usuario_id": context.get("usuario_id", "anonimo"),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(resumen, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------
    # Construcción del prompt contextual
    # ------------------------------------------------------------

    def _build_prompt(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Construye el prompt completo combinando ontología semántica, contexto y ejemplos"""
        p = self.prompt_data
        ejemplos = self._load_examples(limit=6)
        contexto = self._get_context_summary(context)

        prompt = f"""
ROL Y DESCRIPCIÓN:
{p["rol"]} — {p["descripcion"]}

ENTORNO:
{json.dumps(p["entorno"], indent=2, ensure_ascii=False)}

FIRMA COGNITIVA:
{p.get("firma_cognitiva", "")}

ESTRUCTURA DE SALIDA ESPERADA:
{json.dumps(p["estructura_salida"], indent=2, ensure_ascii=False)}

INSTRUCCIÓN DE VISUALIZACIÓN:
{p.get("instruccion_visualizacion", "")}

EJEMPLOS DE PREGUNTA Y ACCIÓN (Finetuning Simulado):
{ejemplos}

CONTEXTO DE SESIÓN:
{contexto}

INSTRUCCIÓN GENERAL:
{p.get("instruccion_general", "")}

PREGUNTA DEL USUARIO:
\"{user_input}\"

Tu respuesta debe ser ÚNICAMENTE un JSON válido con el formato:
{{
  "accion": "string",
  "parametros": {{"clave": "valor"}},
  "visualizacion_sugerida": "string (opcional)"
}}
"""
        return prompt.strip()

    # ------------------------------------------------------------
    # Comunicación con el modelo LLM
    # ------------------------------------------------------------

    def _query_llm(self, prompt: str) -> str:
        """Envía el prompt al modelo y devuelve la respuesta textual"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(self.llm_url, json=payload, timeout=600)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except Exception as e:
            raise RuntimeError(f"Error al comunicarse con el modelo LLM: {e}")

    # ------------------------------------------------------------
    # Interpretación semántica principal
    # ------------------------------------------------------------

    def interpret(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Interpreta la pregunta del usuario en una acción JSON estandarizada"""
        prompt = self._build_prompt(user_input, context)
        llm_output = self._query_llm(prompt)

        try:
            parsed = json.loads(llm_output)
        except json.JSONDecodeError:
            parsed = {"raw_output": llm_output, "accion": "fallback", "parametros": {}, "visualizacion_sugerida": None}

        # Limpieza de campos obligatorios
        parsed.setdefault("accion", "fallback")
        parsed.setdefault("parametros", {})
        parsed.setdefault("visualizacion_sugerida", None)

        # Actualiza memoria de sesión
        self.session_history.append({
            "pregunta": user_input,
            "resultado": parsed,
            "timestamp": datetime.now().isoformat()
        })

        return parsed

    # ------------------------------------------------------------
    # Herramientas de diagnóstico
    # ------------------------------------------------------------

    def resumen_sesion(self, limit: int = 5) -> str:
        """Devuelve las últimas interacciones de la sesión"""
        ultimos = self.session_history[-limit:]
        return json.dumps(ultimos, indent=2, ensure_ascii=False)


# ============================================================
# Ejemplo de uso local (descomentar para test)
# ============================================================
if __name__ == "__main__":
    interpreter = LLMInterpreterV3(
        llm_url="http://localhost:11434/api/generate",
        model="gemma:2b",
        prompt_file="FE_prompt_instruccional_v3.json"
    )

    context = {
        "ultima_accion": "consultar_total_ventas",
        "preferencia_visual": "Sí",
        "usuario_id": "demo_user"
    }

    pregunta = "¿Cuáles fueron los productos más vendidos del trimestre?"
    resultado = interpreter.interpret(pregunta, context)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
