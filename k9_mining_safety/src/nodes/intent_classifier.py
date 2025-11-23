import re
from src.state.state import K9State

def intent_classifier(state: K9State) -> K9State:
    """
    Intent classifier oficial del K9 Mining Safety.
    Primera capa cognitiva del grafo.
    """

    query = (state.user_query or "").lower().strip()

    # --------------------------
    # 1. SALUDOS
    # --------------------------
    greetings = ["hola", "buenas", "buen día", "buenos días", "que tal", "hello", "hi"]
    if any(g in query for g in greetings):
        state.intent = "greeting"
        state.reasoning.append("Intent detected: greeting")
        return state

    # --------------------------
    # 2. PREGUNTAS DEL MODELO PROACTIVO
    # --------------------------
    if "modelo proactivo" in query or "proactive model" in query:
        state.intent = "proactive_model"
        state.reasoning.append("Intent detected: proactive model")
        return state
    # --------------------------
    # 2.1. PREGUNTAS DE BOWTIE
    # --------------------------
    if "bowtie" in query or "bow tie" in query or "corbatín" in query:
        state.intent = "bowtie"
        state.reasoning.append("Intent detected: bowtie")
        return state

    # --------------------------
    # 3. RIESGOS TOP 3 REALES
    # --------------------------
    if "caída" in query or "altura" in query:
        state.intent = "risk_caida_altura"
        state.reasoning.append("Intent detected: risk - caída de altura")
        return state

    if "objetos" in query or "objeto" in query:
        state.intent = "risk_caida_objetos"
        state.reasoning.append("Intent detected: risk - caída de objetos")
        return state

    if "energía" in query or "eléctrica" in query:
        state.intent = "risk_contacto_energia"
        state.reasoning.append("Intent detected: risk - contacto con energía")
        return state
 
    # --------------------------
    # 3.1. CONSULTA GENERAL DE RIESGOS
    # --------------------------
    if "riesgos" in query or "riesgo" in query:
        state.intent = "riesgos"
        state.reasoning.append("Intent detected: general riesgos")
        return state

    # --------------------------
    # 4. CONSULTAS DE MINERÍA GENERAL
    # --------------------------
    mining_keywords = [
        "mina", "rajo", "escondida", "alturas", "faena",
        "campamento", "pala", "camión", "scoop",
        "concentradora", "chancado", "taller", "mantención"
    ]

    if any(k in query for k in mining_keywords):
        state.intent = "mining_general"
        state.reasoning.append("Intent detected: mining general")
        return state

    # --------------------------
    # 5. PREDICTOR (PROYECCIONES)
    # --------------------------
    predictor_keywords = ["predecir", "proyección", "riesgo futuro", "probabilidad", "forecast"]
    if any(k in query for k in predictor_keywords):
        state.intent = "predictor"
        state.reasoning.append("Intent detected: predictor request")
        return state

    # --------------------------
    # 6. ANALYST (INTERPRETACIÓN)
    # --------------------------
    analyst_keywords = ["qué significa", "interpretación", "es bueno", "es malo", "tendencia", "análisis"]
    if any(k in query for k in analyst_keywords):
        state.intent = "analyst"
        state.reasoning.append("Intent detected: analyst interpretation")
        return state

    # --------------------------
    # 7. FALLBACK
    # --------------------------
    state.intent = "general_question"
    state.reasoning.append("Intent detected: general fallback")
    return state
