from __future__ import annotations

import ast
import re
from typing import Any


class EvalError(ValueError):
    pass


_BOOL_REWRITES = {
    r"\btrue\b": "True",
    r"\bfalse\b": "False",
    r"\bnull\b": "None",
}


def eval_expr(expression: str, context: dict[str, Any]) -> Any:
    normalized = expression
    for pattern, replacement in _BOOL_REWRITES.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as exc:
        raise EvalError(f"invalid expression syntax: {expression}") from exc
    evaluator = _SafeEvaluator(context)
    return evaluator.visit(tree.body)


class _SafeEvaluator(ast.NodeVisitor):
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context

    def generic_visit(self, node: ast.AST) -> Any:
        raise EvalError(f"unsupported syntax: {node.__class__.__name__}")

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id not in self.context:
            raise EvalError(f"unknown name: {node.id}")
        return self.context[node.id]

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        value = self.visit(node.value)
        if isinstance(value, dict):
            if node.attr not in value:
                raise EvalError(f"missing key '{node.attr}'")
            return value[node.attr]
        if hasattr(value, node.attr):
            return getattr(value, node.attr)
        raise EvalError(f"cannot resolve attribute '{node.attr}'")

    def visit_Subscript(self, node: ast.Subscript) -> Any:
        value = self.visit(node.value)
        key = self.visit(node.slice)
        try:
            return value[key]
        except (KeyError, IndexError, TypeError) as exc:
            raise EvalError("invalid subscript operation") from exc

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        if isinstance(node.op, ast.And):
            return all(self.visit(value) for value in node.values)
        if isinstance(node.op, ast.Or):
            return any(self.visit(value) for value in node.values)
        raise EvalError("unsupported boolean operator")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        value = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not value
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return +value
        raise EvalError("unsupported unary operator")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        raise EvalError("unsupported binary operator")

    def visit_Compare(self, node: ast.Compare) -> Any:
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            elif isinstance(op, ast.Gt):
                ok = left > right
            elif isinstance(op, ast.GtE):
                ok = left >= right
            elif isinstance(op, ast.Lt):
                ok = left < right
            elif isinstance(op, ast.LtE):
                ok = left <= right
            else:
                raise EvalError("unsupported comparison operator")
            if not ok:
                return False
            left = right
        return True
