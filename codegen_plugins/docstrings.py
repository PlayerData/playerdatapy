"""ariadne-codegen plugin: inject GraphQL schema descriptions into generated enums."""

from __future__ import annotations

import ast

from ariadne_codegen.plugins.base import Plugin
from graphql import GraphQLEnumType


def _docstring_node(text: str) -> ast.Expr:
    return ast.Expr(value=ast.Constant(value=text.strip()))


class EnumDocstringsPlugin(Plugin):
    def generate_enum(
        self, class_def: ast.ClassDef, enum_type: GraphQLEnumType
    ) -> ast.ClassDef:
        new_body: list[ast.stmt] = []

        if enum_type.description:
            new_body.append(_docstring_node(enum_type.description))

        for stmt in class_def.body:
            new_body.append(stmt)
            target_name: str | None = None
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name):
                    target_name = target.id
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                target_name = stmt.target.id

            if target_name and target_name in enum_type.values:
                desc = enum_type.values[target_name].description
                if desc:
                    new_body.append(_docstring_node(desc))

        class_def.body = new_body
        return class_def
