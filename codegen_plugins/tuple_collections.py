"""ariadne-codegen plugin: build query documents from tuples.

graphql-core 3.3 declares every collection on an AST node as a tuple and no
longer converts a list it is handed, and 3.3.0 and 3.3.1 refuse to print a
document that holds one (``TypeError: Invalid AST Node``). ariadne-codegen's
templates hand over lists and do not support 3.3 yet
(mirumee/ariadne-codegen#470), so this plugin wraps each one in ``tuple()``
during codegen.
"""

from __future__ import annotations

import ast

from ariadne_codegen.plugins.base import Plugin

COLLECTION_FIELDS = {"arguments", "definitions", "selections", "variable_definitions"}


def _is_tuple(value: ast.expr) -> bool:
    return isinstance(value, ast.Tuple) or (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "tuple"
    )


def _collections(tree: ast.Module) -> list[ast.expr]:
    return [
        keyword.value
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id.endswith("Node")
        for keyword in call.keywords
        if keyword.arg in COLLECTION_FIELDS and not _is_tuple(keyword.value)
    ]


def with_tuple_collections(code: str) -> str:
    """``code`` with each collection it hands a graphql node wrapped in ``tuple()``."""
    insertions = [
        insertion
        for value in _collections(ast.parse(code))
        for insertion in (
            (value.lineno, value.col_offset, b"tuple("),
            (value.end_lineno, value.end_col_offset, b")"),
        )
    ]
    lines = code.encode().splitlines(keepends=True)
    for line, column, text in sorted(insertions, reverse=True):
        lines[line - 1] = lines[line - 1][:column] + text + lines[line - 1][column:]
    return b"".join(lines).decode()


class TupleCollectionsPlugin(Plugin):
    def generate_client_code(self, generated_code: str) -> str:
        return with_tuple_collections(generated_code)

    def copy_code(self, copied_code: str) -> str:
        return with_tuple_collections(copied_code)
