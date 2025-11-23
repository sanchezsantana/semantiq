from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class K9State(BaseModel):
    user_query: str = ""
    intent: str = ""
    reasoning: List[str] = []
    demo_mode: bool = False
    context: Optional[Dict[str, Any]] = None
    answer: Optional[str] = None   # <-- NUEVO CAMPO
