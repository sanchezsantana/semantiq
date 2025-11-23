import os
from src.state.state import K9State
from config.settings import get_gemini_api_key
from google import genai


def llm_node(state: K9State) -> K9State:
    """
    Nodo 4: LLM Node del K9 Mining Safety.
    Usa GEMINI vía google-genai (SDK oficial nuevo).
    """

    # Si está fuera de dominio → no llamar LLM
    if state.demo_mode:
        state.reasoning.append("LLM Node omitido: demo_mode=True (fuera de dominio).")
        state.answer = (
            "Estoy diseñado para responder sobre minería y seguridad operacional. "
            "Tu pregunta está fuera de ese dominio."
        )
        return state

    # Cargar API KEY
    api_key = get_gemini_api_key()

    # Crear cliente
    client = genai.Client(api_key=api_key)

    prompt = f"""
Eres el agente K9 Mining Safety.
INTENCIÓN: {state.intent}
CONTEXTO: {state.context}
PREGUNTA: {state.user_query}

Da una respuesta clara, breve y profesional.
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        state.answer = response.text
        state.reasoning.append("LLM Node: respuesta generada exitosamente.")

    except Exception as e:
        state.answer = "Error al obtener respuesta del modelo."
        state.reasoning.append(f"LLM Node ERROR: {str(e)}")

    return state

