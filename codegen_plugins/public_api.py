"""ariadne-codegen plugin: re-export hand-written public API from the package root.

The generated ``__init__.py`` only knows about codegen output, so any hand-written
module (``playerdata_api.py`` etc.) silently drops out of the package root on every
regeneration — see PlayerData/analysis-services breakage after v1.11.1. This plugin
adds the exports back during codegen so they survive the nightly regen.
"""

from __future__ import annotations

import ast

from ariadne_codegen.plugins.base import Plugin

PUBLIC_EXPORTS: dict[str, list[str]] = {
    "playerdata_api": ["PlayerDataAPI"],
}


class PublicApiExportsPlugin(Plugin):
    def generate_init_module(self, module: ast.Module) -> ast.Module:
        imports = [
            ast.ImportFrom(module=source, names=[ast.alias(name=name)], level=1)
            for source, names in PUBLIC_EXPORTS.items()
            for name in names
        ]

        last_import_index = max(
            (
                i
                for i, stmt in enumerate(module.body)
                if isinstance(stmt, ast.ImportFrom)
            ),
            default=-1,
        )
        module.body[last_import_index + 1 : last_import_index + 1] = imports

        for stmt in module.body:
            if (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == "__all__"
                and isinstance(stmt.value, ast.List)
            ):
                stmt.value.elts.extend(
                    ast.Constant(value=name)
                    for names in PUBLIC_EXPORTS.values()
                    for name in names
                )
                stmt.value.elts.sort(key=lambda elt: ast.literal_eval(elt))

        return module
