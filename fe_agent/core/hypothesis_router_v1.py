# ============================================================
#  core/hypothesis_router_v1.py
#  Router de hipótesis: n8n vs operaciones locales vs confirmaciones
#  Autor: Eduardo Sánchez Santana
#  Fecha: 2025-10-30
# ============================================================

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
import pandas as pd

from core.fallback_manager import FallbackManager

class HypothesisRouterV1:
    """
    Decide cómo manejar una hipótesis propuesta por el LLM:
    - n8n: acciones operativas del diccionario.
    - local: operaciones de interfaz/memoria/visualización simples.
    - confirm: confirmaciones o re-frases que no requieren ejecución.
    """

    # Prefijos/alias para “operaciones locales” que NO deben pasar por n8n.
    LOCAL_OPS = {
        "ui_repeat_last": "Repetir la última tabla mostrada.",
        "ui_show_chart": "Generar el gráfico del último resultado con el tipo indicado.",
        "ui_change_chart_type": "Cambiar el tipo de gráfico del último resultado.",
        "ui_export_csv": "Exportar la última tabla a CSV.",
        "ctx_set_period": "Actualizar el período por defecto en el contexto.",
        "ctx_set_visual_pref": "Actualizar la preferencia visual (auto/siempre/nunca).",
        "confirm_previous": "Confirmar o validar el resultado anterior sin nueva ejecución.",
    }

    def __init__(self):
        self.fb = FallbackManager()

    # ------------------------------------------------------------
    #  Detección de tipo
    # ------------------------------------------------------------
    def classify(self, candidate: Dict[str, Any]) -> str:
        """
        Clasifica la hipótesis como 'n8n' | 'local' | 'confirm'.
        Reglas:
          - Si 'accion' empieza por 'ui_' o 'ctx_' -> local
          - Si 'accion' == 'confirm_previous'     -> confirm
          - Si 'accion' coincide con patrón operativo -> n8n
          - Si no hay 'accion' -> confirm (no ejecutar)
        """
        accion = (candidate or {}).get("accion")
        if not accion:
            return "confirm"
        if accion.startswith("ui_") or accion.startswith("ctx_"):
            return "local"
        if accion == "confirm_previous":
            return "confirm"
        # Por defecto, suponer acción de n8n (se validará más adelante).
        return "n8n"

    # ------------------------------------------------------------
    #  Ejecución de operaciones locales
    # ------------------------------------------------------------
    def run_local(
        self,
        candidate: Dict[str, Any],
        context_manager,
        last_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta una operación local y devuelve dict {ok, tipo, mensaje, data?}.
        No hace I/O con n8n.
        """
        accion = candidate.get("accion")
        params = candidate.get("parametros", {}) or {}
        msg_base = self.LOCAL_OPS.get(accion, "Operación local")

        try:
            # ui_repeat_last: volver a mostrar la última tabla
            if accion == "ui_repeat_last":
                tabla = context_manager.get("ultima_tabla")
                if not tabla:
                    return {"ok": False, "tipo": "local", "mensaje": "No hay una tabla previa para repetir."}
                return {"ok": True, "tipo": "local", "mensaje": "Repito la última tabla mostrada.", "data": {"tabla": tabla}}

            # ui_show_chart / ui_change_chart_type: marcamos intención para la app
            if accion in ("ui_show_chart", "ui_change_chart_type"):
                tipo = params.get("tipo", "")
                if tipo:
                    context_manager.update("tipo_visualizacion_pendiente", tipo)
                # La app decidirá el render (no graficar aquí).
                return {"ok": True, "tipo": "local", "mensaje": f"Entendido. Prepararé un gráfico en formato {tipo or 'sugerido'}."}

            # ui_export_csv: exportamos última tabla a CSV en /data
            if accion == "ui_export_csv":
                tabla = context_manager.get("ultima_tabla")
                if not tabla:
                    return {"ok": False, "tipo": "local", "mensaje": "No hay datos para exportar."}
                df = pd.DataFrame(tabla)
                path = "data/ultima_tabla_export.csv"
                df.to_csv(path, index=False, encoding="utf-8")
                return {"ok": True, "tipo": "local", "mensaje": f"Exporté la última tabla a {path}.", "data": {"path": path}}

            # ctx_set_period: setea período por defecto en el contexto
            if accion == "ctx_set_period":
                periodo = params.get("periodo")
                if periodo:
                    context_manager.update("periodo_por_defecto", periodo)
                    return {"ok": True, "tipo": "local", "mensaje": f"Período por defecto actualizado a {periodo}."}
                return {"ok": False, "tipo": "local", "mensaje": "No se indicó un período válido."}

            # ctx_set_visual_pref: actualiza preferencia visual
            if accion == "ctx_set_visual_pref":
                pref = params.get("preferencia")
                if pref in ("auto", "siempre", "nunca"):
                    context_manager.set_visual_preference(pref)
                    return {"ok": True, "tipo": "local", "mensaje": f"Preferencia visual actualizada a '{pref}'."}
                return {"ok": False, "tipo": "local", "mensaje": "Preferencia visual no válida (usa: auto/siempre/nunca)."}

            # confirm_previous: confirmación conversacional, sin ejecutar
            if accion == "confirm_previous":
                return {"ok": True, "tipo": "confirm", "mensaje": "Perfecto, quedamos con ese resultado como confirmado."}

            # Fallback si no está implementado
            return {"ok": False, "tipo": "local", "mensaje": f"{msg_base}: aún no implementada."}

        except Exception as e:
            return self.fb.handle(
                user_input="(interno) run_local",
                motivo=str(e),
                tipo="local",
                accion=accion
            )
