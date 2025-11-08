import os
import json
import requests

class LLMInterpreter:
    DEFAULT_CONCEPT_PATH = os.getenv("FE_CONCEPT_PATH", "data/FE_diccionario_conceptos_v2.json")

    def __init__(
        self,
        llm_url: str = "http://localhost:11434/api/generate",
        model: str = "gemma:2b",
        conceptos_path: str = DEFAULT_CONCEPT_PATH,
    ):
        self.llm_url = llm_url
        self.model = model
        self.conceptos_path = conceptos_path
        self.conceptos = {}
        self._load_assets()

    # ============================================================
    #   CARGA DE ARCHIVOS Y CONCEPTOS
    # ============================================================
    def _load_assets(self):
        """Carga el diccionario de conceptos comerciales"""
        try:
            if os.path.exists(self.conceptos_path):
                with open(self.conceptos_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.conceptos = data.get("conceptos", {})
                print(f"[INFO] Diccionario de conceptos cargado desde {self.conceptos_path} ({len(self.conceptos)} conceptos).")
            else:
                print(f"[WARN] No se encontró el diccionario de conceptos en {self.conceptos_path}.")
        except Exception as e:
            print(f"[ERROR] No se pudo cargar el diccionario de conceptos: {e}")

    # ============================================================
    #   MÉTODO: RESUMEN DE CONCEPTOS PARA EL LLM
    # ============================================================
    def _concept_summary(self, max_items: int = 20) -> str:
        """Genera un resumen textual con los conceptos principales"""
        if not self.conceptos:
            return "No hay conceptos cargados."
        summary_lines = []
        for i, (key, val) in enumerate(self.conceptos.items()):
            if i >= max_items:
                break
            desc = val.get("descripcion", "")
            summary_lines.append(f"- {key}: {desc}")
        return "\n".join(summary_lines)

    # ============================================================
    #   MÉTODO: CONSTRUCCIÓN DE PROMPT CON CONTEXTO SEMÁNTICO
    # ============================================================
    def _build_prompt(self, user_input: str) -> str:
        """Construye el prompt que se enviará al modelo Gemma"""
        conceptos_context = self._concept_summary()
        prompt = f"""
Eres un intérprete semántico especializado en análisis comercial para una ferretería en Chile.
Tu tarea es entender la intención del usuario y devolver una instrucción estructurada en formato JSON
que indique la acción y los parámetros relevantes.

Conceptos comerciales clave del dominio:
{conceptos_context}

Instrucción del usuario:
"{user_input}"

Responde únicamente con un JSON con el formato:
{{
  "accion": "nombre_de_accion",
  "parametros": {{"param1": "valor1", "param2": "valor2"}}
}}
"""
        return prompt.strip()

    # ============================================================
    #   MÉTODO: ENVÍO DE PETICIÓN AL LLM (GEMMA)
    # ============================================================
    def interpret(self, user_input: str) -> dict:
        """Envía la consulta al LLM y obtiene la instrucción estructurada"""
        prompt = self._build_prompt(user_input)
        payload = {"model": self.model, "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.llm_url, json=payload)
            response.raise_for_status()
            result = response.json()
            output_text = result.get("response", "").strip()

            # Intentar decodificar JSON del resultado
            try:
                parsed = json.loads(output_text)
                return parsed
            except json.JSONDecodeError:
                print("[WARN] No se pudo decodificar JSON, devolviendo texto sin procesar.")
                return {"raw_output": output_text}

        except Exception as e:
            print(f"[ERROR] Error al conectar con el LLM: {e}")
            return {"error": str(e)}

# ============================================================
#   EJEMPLO DE USO LOCAL
# ============================================================
if __name__ == "__main__":
    interpreter = LLMInterpreter()
    pregunta = "¿Cuál fue el margen global del último trimestre?"
    resultado = interpreter.interpret(pregunta)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
