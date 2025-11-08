# ============================================================
#  core/ambiguity_manager_v2.py
#  Versión 2 - Detección y gestión contextual de ambigüedades
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-29
# ============================================================

import re
from typing import Dict, Any, Optional


class AmbiguityManagerV2:
    """
    Detecta y gestiona ambigüedades en las entradas del usuario.
    Si encuentra términos vagos o incompletos, genera una pregunta aclaratoria
    y la registra en el ContextManager si está disponible.
    """

    def __init__(self):
        self.patrones_ambiguos = [
            r"\b(algo|cosas|eso|aquello|varias|diferentes)\b",
            r"\b(puedes|podrías|me dices|quiero saber)\b$",
            r"\b(últimos|recientes|anteriores)\b$",
            r"\b(haz|realiza|muestra)\b$",
            r"(\?)\s*$"  # preguntas abiertas sin sujeto claro
        ]
        self.frases_genericas = [
            "No estoy seguro de a qué te refieres exactamente.",
            "¿Podrías especificar a qué período, producto o cliente te refieres?",
            "Necesito un poco más de detalle para ayudarte correctamente.",
            "¿Podrías precisar el alcance de la pregunta?"
        ]

    # ------------------------------------------------------------
    # DETECCIÓN
    # ------------------------------------------------------------
    def detectar_ambigüedad(self, texto: str) -> bool:
        texto = texto.lower().strip()
        for p in self.patrones_ambiguos:
            if re.search(p, texto):
                return True
        return False

    def generar_pregunta_clarificadora(self) -> str:
        """Devuelve una pregunta aclaratoria predefinida."""
        import random
        return random.choice(self.frases_genericas)

    # ------------------------------------------------------------
    # PROCESAMIENTO PRINCIPAL
    # ------------------------------------------------------------
    def procesar_input(self, user_input: str, context_manager=None) -> Dict[str, Any]:
        """
        Analiza una entrada y determina si requiere clarificación.
        Si hay ambigüedad, registra la pregunta aclaratoria en el contexto.
        """
        resultado = {
            "estado": "claro",
            "mensaje": user_input,
            "requiere_clarificacion": False
        }

        if self.detectar_ambigüedad(user_input):
            pregunta = self.generar_pregunta_clarificadora()
            resultado = {
                "estado": "ambiguo",
                "mensaje": pregunta,
                "requiere_clarificacion": True
            }
            if context_manager:
                context_manager.update("clarificacion_pendiente", pregunta)

        return resultado
