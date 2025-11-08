# ============================================================
#  core/language_generator.py
#  Versión 1 - Generador determinista de lenguaje natural
# ============================================================

import random

class LanguageGenerator:
    """
    Crea respuestas en lenguaje natural a partir de los datos devueltos por n8n
    o resultados calculados localmente.
    """

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self):
        """Plantillas simples de respuesta"""
        return {
            "ventas": [
                "Durante el período analizado, las ventas totales alcanzaron ${valor:,}.",
                "El total de ventas fue de ${valor:,}, mostrando una tendencia {tendencia}."
            ],
            "margen": [
                "El margen global del período fue de {valor}%.",
                "Se registró una rentabilidad promedio de {valor}%."
            ],
            "stock": [
                "Actualmente existen {valor} productos en stock.",
                "El inventario cuenta con {valor} unidades disponibles."
            ]
        }

    def generate(self, action_name: str, data: dict) -> str:
        """Genera texto basado en la acción y los datos recibidos."""
        if not data:
            return "No se obtuvieron datos para esta consulta."

        template_group = self.templates.get(action_name.split("_")[0], ["Resultado disponible."])
        template = random.choice(template_group)

        # Buscar el valor principal en el diccionario
        valor = data.get("valor") or data.get("total") or data.get("resultado") or "N/A"
        tendencia = data.get("tendencia", "estable")

        try:
            return template.format(valor=valor, tendencia=tendencia)
        except Exception:
            return "Información procesada correctamente, pero sin plantilla específica."
