# ============================================================
#  core/ambiguity_manager.py
#  Primera versión funcional - Agente FE
# ============================================================
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-28
#  Descripción:
#  Módulo para detectar y gestionar ambigüedades en las preguntas
#  del usuario antes de que sean interpretadas por el LLM.
# ============================================================

import re

class AmbiguityManager:
    """
    El AmbiguityManager detecta posibles ambigüedades en la consulta del usuario,
    genera preguntas aclaratorias y mantiene un estado temporal hasta recibir
    una respuesta clara. Se integra antes del LLMInterpreter.
    """

    def __init__(self):
        self.pending_clarification = None
        self.patterns = self._load_patterns()

    # ------------------------------------------------------------
    # Carga de patrones de ambigüedad
    # ------------------------------------------------------------
    def _load_patterns(self):
        """
        Define un conjunto inicial de patrones de ambigüedad
        comunes en el dominio comercial de la ferretería.
        """
        return {
            "ventas": [
                "¿Te refieres a las ventas totales, por producto o por cliente?",
                "¿Deseas que considere un período específico (mensual, trimestral, anual)?"
            ],
            "margen": [
                "¿Quieres ver el margen global o el margen por trimestre?",
                "¿Debo calcular el margen como porcentaje o en pesos chilenos?"
            ],
            "clientes": [
                "¿Quieres ver clientes nuevos, frecuentes o estratégicos?",
                "¿Deseas comparar clientes entre períodos?"
            ],
            "compras": [
                "¿Te refieres a compras totales o a compras por proveedor?",
                "¿Quieres analizar las compras en un período específico?"
            ],
            "stock": [
                "¿Quieres ver el stock total, por producto o solo los que están bajo mínimo?",
                "¿Deseas incluir también productos inmovilizados?"
            ]
        }

    # ------------------------------------------------------------
    # Detección de ambigüedad
    # ------------------------------------------------------------
    def detectar_ambigüedad(self, user_input: str) -> bool:
        """
        Analiza la entrada del usuario y detecta si falta contexto
        suficiente para ejecutar una acción con certeza.
        """
        text = user_input.lower()
        for keyword, preguntas in self.patterns.items():
            if keyword in text:
                # Si no se especifica un detalle como período o categoría
                if not re.search(r"(mensual|trimestral|anual|por producto|por cliente|total)", text):
                    self.pending_clarification = preguntas
                    return True
        return False

    # ------------------------------------------------------------
    # Generación de pregunta aclaratoria
    # ------------------------------------------------------------
    def generar_pregunta_clarificadora(self) -> str:
        """
        Devuelve una pregunta de aclaración basada en la ambigüedad detectada.
        """
        if not self.pending_clarification:
            return ""
        pregunta = " ".join(self.pending_clarification)
        return f"🤔 {pregunta}"

    # ------------------------------------------------------------
    # Limpieza de estado
    # ------------------------------------------------------------
    def limpiar_estado(self):
        """Reinicia el estado de ambigüedad después de una aclaración."""
        self.pending_clarification = None

    # ------------------------------------------------------------
    # Integración con contexto
    # ------------------------------------------------------------
    def procesar_input(self, user_input: str) -> dict:
        """
        Evalúa si el input es ambiguo y devuelve un resultado estructurado
        para que Streamlit pueda decidir si continuar o pedir aclaración.
        """
        if self.detectar_ambigüedad(user_input):
            return {
                "estado": "ambiguo",
                "mensaje": self.generar_pregunta_clarificadora(),
                "requiere_clarificacion": True
            }
        return {
            "estado": "claro",
            "mensaje": user_input,
            "requiere_clarificacion": False
        }


# ============================================================
# Ejemplo de uso local
# ============================================================
if __name__ == "__main__":
    am = AmbiguityManager()

    ejemplos = [
        "Muéstrame las ventas",
        "Cuál fue el margen",
        "Ver clientes nuevos del trimestre",
        "Analiza las compras totales de proveedores"
    ]

    for pregunta in ejemplos:
        resultado = am.procesar_input(pregunta)
        print(f"\n🧩 Entrada: {pregunta}")
        print(f"→ Resultado: {resultado}")
