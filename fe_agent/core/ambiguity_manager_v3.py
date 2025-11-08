# ============================================================
#  core/ambiguity_manager_v3.py
#  Gestor de ambigüedades con detección fuerte y fuera de dominio
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-31
# ============================================================

import re
from typing import Dict, Any, List

FERRETERIA_DOMINIOS = [
    "ventas", "compras", "productos", "clientes", "proveedores",
    "margen", "ganancias", "stock", "inventario", "rotación", "categorías"
]


class AmbiguityManagerV3:
    """
    Detección de ambigüedades con:
      - detección fuerte por heurística
      - filtro de fuera de dominio
      - integración con DisambiguationManagerV2
    """

    def __init__(self):
        self.patterns_vagos = [
            r"\besto\b", r"\baquello\b", r"\ballo\b", r"\bcosas\b",
            r"\bdatos\b", r"\binformación\b", r"\bresultado\b"
        ]
        self.pat_question = re.compile(r"\?$")

    # ------------------------------------------------------------
    # MÉTODO PRINCIPAL
    # ------------------------------------------------------------
    def procesar_input(self, texto: str) -> Dict[str, Any]:
        texto = (texto or "").strip().lower()

        if not texto or len(texto) < 5:
            return self._respuesta("clarify", "La pregunta parece incompleta o muy corta.")

        if self._fuera_de_dominio(texto):
            return self._respuesta("out_of_scope", "La pregunta parece estar fuera del dominio comercial de la ferretería.")

        if any(re.search(p, texto) for p in self.patterns_vagos):
            return self._respuesta("clarify", "La pregunta es demasiado general, necesito más detalle.")

        if self.detectar_ambigüedad_fuerte(texto):
            return self._respuesta("clarify", "Parece una pregunta ambigua o múltiple.")

        return {"requiere_clarificacion": False, "motivo": None}

    # ------------------------------------------------------------
    # FUNCIONES AUXILIARES
    # ------------------------------------------------------------
    def detectar_ambigüedad_fuerte(self, texto: str) -> bool:
        # Corto, doble pregunta, o términos opuestos
        if len(texto.split()) <= 3:
            return True
        if texto.count("?") > 1:
            return True
        if " o " in texto and "y" in texto:
            return True
        return False

    def _fuera_de_dominio(self, texto: str) -> bool:
        return not any(d in texto for d in FERRETERIA_DOMINIOS)

    def _respuesta(self, tipo: str, mensaje: str) -> Dict[str, Any]:
        return {
            "requiere_clarificacion": True,
            "tipo": tipo,
            "mensaje": mensaje
        }
