from src.state.state import K9State

def load_context(state: K9State) -> K9State:
    """
    Nodo 3 del grafo K9 Mining Safety.
    Carga el contexto operativo mínimo que el agente necesita para razonar.
    Versión 0.1: contexto estático, sin Redis aún.
    """

    context = {
        "areas_operacionales": [
            "Mina Rajo",
            "Planta Concentradora",
            "Chancado",
            "Taller de Mantención",
            "Campamento",
        ],
        "top_riesgos_escondida": [
            "Caída de altura",
            "Caída de objetos",
            "Contacto con energía"
        ],
        "modelo_proactivo_definicion": (
            "El Modelo Proactivo es una metodología predictiva usada en minería "
            "para anticipar riesgos operacionales en ventanas de corto plazo."
        ),
        "tipos_eventos": {
            "NM": "Near Miss (evento sin lesión pero con potencial)",
            "OPG": "Oportunidad de mejora",
            "OCC": "Observación de conducta crítica",
            "INC": "Incidente",
            "HZD": "Peligro detectado"
        },
        "version_contexto": "0.1"
    }

    # Guardamos el contexto en el estado
    state.context = context
    state.reasoning.append("Load Context: contexto operativo básico cargado (v0.1).")

    return state
