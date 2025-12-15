from langgraph.graph import StateGraph, START, END

from src.state.state import K9State

# --- Nodos base del pipeline ---
from src.nodes.intent_classifier import intent_classifier
from src.nodes.domain_guardrail import domain_guardrail
from src.nodes.load_context import load_context
from src.nodes.llm_node import llm_node
from src.nodes.router import router_node
from src.nodes.analyst_node import analyst_node
from src.nodes.narrative_node import narrative_node

# --- Nodos cognitivos K9 ---
from src.nodes.proactive_model_node import proactive_model_node
from src.nodes.riesgos_node import riesgos_node
from src.nodes.fallback_node import fallback_node
from src.nodes.semantic_retrieval_node import semantic_retrieval_node
from src.nodes.bowtie_node import bowtie_node


def build_k9_graph():
    graph = StateGraph(K9State)

    # --------------------------------------------------------------------------------------------------------------
    #                                           NODOS BASE DEL PIPELINE
    # --------------------------------------------------------------------------------------------------------------
    graph.add_node("intent", intent_classifier)
    graph.add_node("guardrail", domain_guardrail)
    graph.add_node("context", load_context)
    graph.add_node("analyst", analyst_node)

    # Router
    graph.add_node("router", router_node)

    # Ramas funcionales
    graph.add_node("llm", llm_node)
    graph.add_node("semantic_retrieval", semantic_retrieval_node)
    graph.add_node("proactive_model", proactive_model_node)
    graph.add_node("riesgos", riesgos_node)
    graph.add_node("bowtie", bowtie_node)
    graph.add_node("fallback", fallback_node)

    # Narrative (SALIDA ÚNICA)
    graph.add_node("narrative", narrative_node)

    # --------------------------------------------------------------------------------------------------------------
    #                                           FLUJO PRINCIPAL
    # --------------------------------------------------------------------------------------------------------------
    graph.add_edge(START, "intent")
    graph.add_edge("intent", "guardrail")
    graph.add_edge("guardrail", "context")
    graph.add_edge("context", "analyst")
    graph.add_edge("analyst", "router")

    # --------------------------------------------------------------------------------------------------------------
    #                                           ROUTER (CONDITIONAL EDGES)
    # --------------------------------------------------------------------------------------------------------------
    def route_intent(state: K9State):
        intent = state.intent

        valid_intents = [
            "greeting",
            "proactive_model",
            "riesgos",
            "mining_general",
            "general_question",
            "bowtie",
        ]

        if intent not in valid_intents:
            state.reasoning.append(
                f"Router Node: intent '{intent}' no reconocido → fallback."
            )
            return "fallback"

        state.reasoning.append(f"Router Node: routing intent '{intent}'.")
        return intent

    graph.add_conditional_edges(
        "router",
        route_intent,
        {
            "greeting": "llm",
            "proactive_model": "proactive_model",
            "riesgos": "riesgos",
            "mining_general": "semantic_retrieval",
            "general_question": "semantic_retrieval",
            "bowtie": "bowtie",
            "fallback": "fallback",
        }
    )

    # --------------------------------------------------------------------------------------------------------------
    #                                           SALIDAS → NARRATIVE → END
    # --------------------------------------------------------------------------------------------------------------
    graph.add_edge("llm", "narrative")
    graph.add_edge("proactive_model", "narrative")
    graph.add_edge("riesgos", "narrative")
    graph.add_edge("semantic_retrieval", "narrative")
    graph.add_edge("bowtie", "narrative")
    graph.add_edge("fallback", "narrative")

    graph.add_edge("narrative", END)

    return graph.compile()
