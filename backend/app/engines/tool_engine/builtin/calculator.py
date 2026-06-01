"""Built-in tool: mathematical calculator using sympy."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.engines.tool_engine.registry import ToolDef

logger = logging.getLogger(__name__)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "expression": {
            "type": "string",
            "description": "Mathematical expression to evaluate (e.g., '2**10', 'sqrt(144)', 'integrate(x**2, x)')",
        },
    },
    "required": ["expression"],
}


async def _execute(params: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a mathematical expression safely using sympy."""
    expression = params["expression"]

    try:
        import sympy
        from sympy.parsing.sympy_parser import parse_expr

        def _eval():
            # Only allow safe math operations
            allowed_names = {
                "sqrt": sympy.sqrt,
                "log": sympy.log,
                "ln": sympy.ln,
                "sin": sympy.sin,
                "cos": sympy.cos,
                "tan": sympy.tan,
                "pi": sympy.pi,
                "e": sympy.E,
                "oo": sympy.oo,
                "inf": sympy.oo,
                "integrate": sympy.integrate,
                "diff": sympy.diff,
                "sum": sympy.summation,
                "factorial": sympy.factorial,
                "abs": sympy.Abs,
            }
            result = parse_expr(expression, local_dict=allowed_names)
            return sympy.simplify(result)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _eval)
        return {"result": str(result), "numeric": float(result) if result.is_number else None}
    except ImportError:
        logger.warning("sympy not installed, using eval fallback")
        try:
            # Basic fallback with restricted eval
            result = eval(expression, {"__builtins__": {}}, {})
            return {"result": str(result), "numeric": float(result)}
        except Exception as e:
            return {"error": f"Cannot evaluate: {e}"}
    except Exception as e:
        return {"error": f"Calculation error: {e}"}


calculator_tool = ToolDef(
    name="calculator",
    description="Evaluate mathematical expressions. Supports arithmetic, algebra, calculus, and trigonometry.",
    tool_type="builtin",
    input_schema=INPUT_SCHEMA,
    handler=_execute,
    permissions=["tool:calculator"],
)
