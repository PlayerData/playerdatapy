"""Generate language-agnostic GraphQL schema reference from schema.graphql."""

from __future__ import annotations

from pathlib import Path

import mkdocs_gen_files
from graphql import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLUnionType,
    build_schema,
)


SCHEMA_PATH = Path("schema.graphql")
OUT_ROOT = Path("schema")


def _type_url(t) -> str | None:
    """Return relative URL within docs/schema/ to the page for type `t`, or None."""
    if isinstance(t, (GraphQLNonNull, GraphQLList)):
        return _type_url(t.of_type)
    if isinstance(t, GraphQLObjectType):
        return f"../objects/{t.name}.md"
    if isinstance(t, GraphQLInputObjectType):
        return f"../inputs/{t.name}.md"
    if isinstance(t, GraphQLEnumType):
        return f"../enums/{t.name}.md"
    if isinstance(t, GraphQLInterfaceType):
        return f"../interfaces/{t.name}.md"
    if isinstance(t, GraphQLUnionType):
        return f"../unions/{t.name}.md"
    if isinstance(t, GraphQLScalarType):
        return f"../scalars/{t.name}.md"
    return None


def _render_type(t) -> str:
    """Render a type to a string with backtick-quoted type names linked to their pages."""
    if isinstance(t, GraphQLNonNull):
        return _render_type(t.of_type) + "!"
    if isinstance(t, GraphQLList):
        return "[" + _render_type(t.of_type) + "]"
    url = _type_url(t)
    if url:
        return f"[`{t.name}`]({url})"
    return f"`{t.name}`"


def _named(t):
    while isinstance(t, (GraphQLNonNull, GraphQLList)):
        t = t.of_type
    return t


def _render_args(args: dict) -> str:
    if not args:
        return ""
    rows = ["| Name | Type | Description |", "| --- | --- | --- |"]
    for name, arg in args.items():
        desc = (arg.description or "").replace("\n", " ").strip()
        rows.append(f"| `{name}` | {_render_type(arg.type)} | {desc} |")
    return "\n".join(rows)


def _render_fields(fields: dict, *, include_args: bool) -> str:
    if not fields:
        return "_No fields._\n"
    out: list[str] = []
    for name, field in fields.items():
        desc = (field.description or "").strip()
        out.append(f"### `{name}`\n")
        if desc:
            out.append(desc + "\n")
        out.append(f"**Returns:** {_render_type(field.type)}\n")
        if include_args and field.args:
            out.append("**Arguments:**\n")
            out.append(_render_args(field.args) + "\n")
        out.append("")
    return "\n".join(out)


def _write_operation_page(kind: str, name: str, field) -> Path:
    path = OUT_ROOT / kind / f"{name}.md"
    desc = (field.description or "").strip()
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(f"# `{name}`\n\n")
        if desc:
            f.write(desc + "\n\n")
        f.write(f"**Returns:** {_render_type(field.type)}\n\n")
        if field.args:
            f.write("## Arguments\n\n")
            f.write(_render_args(field.args) + "\n\n")
        named = _named(field.type)
        ret_url = _type_url(named)
        if ret_url:
            f.write(f"See the returned type: [`{named.name}`]({ret_url})\n")
    return path


def _write_object_page(kind: str, t: GraphQLObjectType) -> Path:
    path = OUT_ROOT / kind / f"{t.name}.md"
    desc = (t.description or "").strip()
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(f"# `{t.name}`\n\n")
        if desc:
            f.write(desc + "\n\n")
        if t.interfaces:
            iface_links = ", ".join(_render_type(i) for i in t.interfaces)
            f.write(f"**Implements:** {iface_links}\n\n")
        f.write("## Fields\n\n")
        f.write(_render_fields(t.fields, include_args=True))
    return path


def _write_input_page(t: GraphQLInputObjectType) -> Path:
    path = OUT_ROOT / "inputs" / f"{t.name}.md"
    desc = (t.description or "").strip()
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(f"# `{t.name}`\n\n")
        if desc:
            f.write(desc + "\n\n")
        f.write("## Fields\n\n")
        rows = ["| Name | Type | Description |", "| --- | --- | --- |"]
        for name, field in t.fields.items():
            field_desc = (field.description or "").replace("\n", " ").strip()
            rows.append(f"| `{name}` | {_render_type(field.type)} | {field_desc} |")
        f.write("\n".join(rows) + "\n")
    return path


def _write_enum_page(t: GraphQLEnumType) -> Path:
    path = OUT_ROOT / "enums" / f"{t.name}.md"
    desc = (t.description or "").strip()
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(f"# `{t.name}`\n\n")
        if desc:
            f.write(desc + "\n\n")
        f.write("## Values\n\n")
        rows = ["| Value | Description |", "| --- | --- |"]
        for name, value in t.values.items():
            val_desc = (value.description or "").replace("\n", " ").strip()
            rows.append(f"| `{name}` | {val_desc} |")
        f.write("\n".join(rows) + "\n")
    return path


def _write_scalar_page(t: GraphQLScalarType) -> Path:
    path = OUT_ROOT / "scalars" / f"{t.name}.md"
    desc = (t.description or "").strip()
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(f"# `{t.name}`\n\n")
        if desc:
            f.write(desc + "\n\n")
        else:
            f.write(f"Scalar type `{t.name}`.\n")
    return path


def _write_interface_page(t: GraphQLInterfaceType) -> Path:
    path = OUT_ROOT / "interfaces" / f"{t.name}.md"
    desc = (t.description or "").strip()
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(f"# `{t.name}`\n\n")
        if desc:
            f.write(desc + "\n\n")
        f.write("## Fields\n\n")
        f.write(_render_fields(t.fields, include_args=True))
    return path


def _write_union_page(t: GraphQLUnionType) -> Path:
    path = OUT_ROOT / "unions" / f"{t.name}.md"
    desc = (t.description or "").strip()
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(f"# `{t.name}`\n\n")
        if desc:
            f.write(desc + "\n\n")
        f.write("## Possible types\n\n")
        for member in t.types:
            f.write(f"- {_render_type(member)}\n")
    return path


def _write_index(kind: str, label: str, items: list[tuple[str, str]]) -> None:
    """items: list of (name, description) sorted alphabetically."""
    path = OUT_ROOT / kind / "index.md"
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(f"# {label}\n\n")
        if not items:
            f.write("_None._\n")
            return
        f.write("| Name | Description |\n| --- | --- |\n")
        for name, desc in items:
            short = desc.split("\n", 1)[0].strip()
            f.write(f"| [`{name}`]({name}.md) | {short} |\n")


def _write_schema_landing(counts: dict[str, int]) -> None:
    with mkdocs_gen_files.open(OUT_ROOT / "index.md", "w") as f:
        f.write("# GraphQL Schema\n\n")
        f.write(
            "Language-agnostic reference rendered directly from `schema.graphql`. "
            "Names, field casing, and types match the wire format — what you'd send and receive over HTTP regardless of client library.\n\n"
        )
        f.write("## Sections\n\n")
        sections = [
            ("queries", "Queries", "Read operations exposed on `Query`"),
            ("mutations", "Mutations", "Write operations exposed on `Mutation`"),
            ("objects", "Object types", "Composite types returned by queries"),
            ("interfaces", "Interfaces", "Abstract types implemented by objects"),
            ("unions", "Unions", "Sum types — one of several object types"),
            ("inputs", "Input types", "Argument shapes accepted by operations"),
            ("enums", "Enums", "Fixed string-valued enumerations"),
            ("scalars", "Scalars", "Primitive types (built-in + custom)"),
        ]
        for slug, label, blurb in sections:
            count = counts.get(slug, 0)
            f.write(f"- **[{label}]({slug}/index.md)** ({count}) — {blurb}\n")


def _write_summary(
    operations: dict[str, list[str]],
    type_pages: dict[str, list[str]],
) -> None:
    with mkdocs_gen_files.open(OUT_ROOT / "SUMMARY.md", "w") as f:
        f.write("- [Overview](index.md)\n")
        for slug, label in [
            ("queries", "Queries"),
            ("mutations", "Mutations"),
            ("objects", "Object types"),
            ("interfaces", "Interfaces"),
            ("unions", "Unions"),
            ("inputs", "Input types"),
            ("enums", "Enums"),
            ("scalars", "Scalars"),
        ]:
            items = sorted(set(operations.get(slug, []) + type_pages.get(slug, [])))
            if not items:
                continue
            f.write(f"- {label}\n")
            f.write(f"    - [Overview]({slug}/index.md)\n")
            for name in items:
                f.write(f"    - [{name}]({slug}/{name}.md)\n")


def _short_desc(d: str | None) -> str:
    if not d:
        return ""
    return d.replace("\n", " ").strip()


def main() -> None:
    if not SCHEMA_PATH.exists():
        print(f"[gen_schema] {SCHEMA_PATH} not found, skipping")
        return

    schema: GraphQLSchema = build_schema(SCHEMA_PATH.read_text())

    operations: dict[str, list[str]] = {"queries": [], "mutations": []}
    type_pages: dict[str, list[str]] = {
        "objects": [],
        "interfaces": [],
        "unions": [],
        "inputs": [],
        "enums": [],
        "scalars": [],
    }
    counts: dict[str, int] = {}

    queries_index: list[tuple[str, str]] = []
    if schema.query_type:
        for name, field in schema.query_type.fields.items():
            _write_operation_page("queries", name, field)
            operations["queries"].append(name)
            queries_index.append((name, _short_desc(field.description)))

    mutations_index: list[tuple[str, str]] = []
    if schema.mutation_type:
        for name, field in schema.mutation_type.fields.items():
            _write_operation_page("mutations", name, field)
            operations["mutations"].append(name)
            mutations_index.append((name, _short_desc(field.description)))

    object_index: list[tuple[str, str]] = []
    interface_index: list[tuple[str, str]] = []
    union_index: list[tuple[str, str]] = []
    input_index: list[tuple[str, str]] = []
    enum_index: list[tuple[str, str]] = []
    scalar_index: list[tuple[str, str]] = []

    operation_type_names = set()
    if schema.query_type:
        operation_type_names.add(schema.query_type.name)
    if schema.mutation_type:
        operation_type_names.add(schema.mutation_type.name)
    if schema.subscription_type:
        operation_type_names.add(schema.subscription_type.name)

    for name, t in schema.type_map.items():
        if name.startswith("__"):
            continue
        if name in operation_type_names:
            continue

        if isinstance(t, GraphQLObjectType):
            _write_object_page("objects", t)
            type_pages["objects"].append(name)
            object_index.append((name, _short_desc(t.description)))
        elif isinstance(t, GraphQLInterfaceType):
            _write_interface_page(t)
            type_pages["interfaces"].append(name)
            interface_index.append((name, _short_desc(t.description)))
        elif isinstance(t, GraphQLUnionType):
            _write_union_page(t)
            type_pages["unions"].append(name)
            union_index.append((name, _short_desc(t.description)))
        elif isinstance(t, GraphQLInputObjectType):
            _write_input_page(t)
            type_pages["inputs"].append(name)
            input_index.append((name, _short_desc(t.description)))
        elif isinstance(t, GraphQLEnumType):
            _write_enum_page(t)
            type_pages["enums"].append(name)
            enum_index.append((name, _short_desc(t.description)))
        elif isinstance(t, GraphQLScalarType):
            _write_scalar_page(t)
            type_pages["scalars"].append(name)
            scalar_index.append((name, _short_desc(t.description)))

    _write_index("queries", "Queries", sorted(queries_index))
    _write_index("mutations", "Mutations", sorted(mutations_index))
    _write_index("objects", "Object types", sorted(object_index))
    _write_index("interfaces", "Interfaces", sorted(interface_index))
    _write_index("unions", "Unions", sorted(union_index))
    _write_index("inputs", "Input types", sorted(input_index))
    _write_index("enums", "Enums", sorted(enum_index))
    _write_index("scalars", "Scalars", sorted(scalar_index))

    counts = {
        "queries": len(queries_index),
        "mutations": len(mutations_index),
        "objects": len(object_index),
        "interfaces": len(interface_index),
        "unions": len(union_index),
        "inputs": len(input_index),
        "enums": len(enum_index),
        "scalars": len(scalar_index),
    }
    _write_schema_landing(counts)
    _write_summary(operations, type_pages)


main()
