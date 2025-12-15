from src.state.state import K9State

def load_context(state: K9State) -> K9State:
    """
    Nodo 3 del grafo K9 Mining Safety.
    Carga el contexto operativo mínimo que el agente necesita para razonar.
    Versión 0.2: alineado con K9State v3.2.
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
        "version_contexto": "0.2"
    }

    # Guardamos el contexto estructural en el state v3.2
    state.context_bundle = context
    state.reasoning.append("Load Context: contexto estructural cargado (v0.2).")

    return state
