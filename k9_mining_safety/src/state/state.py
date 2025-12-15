from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class K9State(BaseModel):
    # Input
    user_query: str = ""
    intent: str = ""

    # Trazabilidad de ejecución (pipeline)
    reasoning: List[str] = []

    # Flags de ejecución
    demo_mode: bool = False

    # Contexto estructural
    context_bundle: Optional[Dict[str, Any]] = None

    # Señales temporales / STDE
    signals: Optional[Dict[str, Any]] = None

    # Evento activo (ej. lunes crítico)
    active_event: Optional[Dict[str, Any]] = None

    # Análisis cognitivo estructurado (AnalystNode)
    analysis: Optional[Dict[str, Any]] = None

    # Salida final
    answer: Optional[str] = None
