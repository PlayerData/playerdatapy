"""Generate per-class API reference pages at build time."""

from __future__ import annotations

import builtins
import importlib
import inspect
import typing
from collections import defaultdict
from pathlib import Path

import mkdocs_gen_files

try:
    _enums = importlib.import_module("playerdatapy.enums")
    for _name in dir(_enums):
        if _name.startswith("_"):
            continue
        if not hasattr(builtins, _name):
            setattr(builtins, _name, getattr(_enums, _name))
except Exception as _exc:
    print(f"[gen_ref] could not preload enums: {_exc}")


SECTIONS: list[tuple[str, list[str]]] = [
    ("PlayerDataAPI", ["playerdatapy.playerdata_api"]),
    ("Authentication", ["playerdatapy.gqlauth"]),
    ("GraphQL Client", ["playerdatapy.gqlclient"]),
    ("Queries", ["playerdatapy.custom_queries"]),
    ("Mutations", ["playerdatapy.custom_mutations"]),
    ("Fields", ["playerdatapy.custom_fields"]),
    ("Input Types", ["playerdatapy.input_types"]),
    ("Enums", ["playerdatapy.enums"]),
    ("Exceptions", ["playerdatapy.exceptions"]),
]

SECTION_INTROS: dict[str, str] = {
    "PlayerDataAPI": "Recommended entry point. Wraps authentication and runs typed queries/mutations.",
    "Authentication": "OAuth2 flows and token persistence. Used internally by `PlayerDataAPI`.",
    "GraphQL Client": "Low-level async HTTP client. Use for raw GraphQL strings.",
    "Queries": "Typed query builders generated from the schema. Pass to `PlayerDataAPI.run_queries`.",
    "Mutations": "Typed mutation builders. Require Authorisation Code Grant — Client Credentials is read-only.",
    "Fields": "Field builders used when composing queries and mutations.",
    "Input Types": "Pydantic models for query/mutation arguments. Field descriptions come from the schema.",
    "Enums": "String-valued enumerations from the schema. Class and member docstrings come from schema descriptions.",
    "Exceptions": "Error types raised by the GraphQL client.",
}


def _slug(name: str) -> str:
    return name.replace(" ", "-").lower()


def _public_classes(module) -> list[tuple[str, type]]:
    out: list[tuple[str, type]] = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if name.startswith("_"):
            continue
        if obj.__module__ != module.__name__:
            continue
        out.append((name, obj))
    out.sort(key=lambda x: x[0])
    return out


def _referenced_type_names(annotation, known_names: set[str]) -> set[str]:
    out: set[str] = set()
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    if origin is None and args == ():
        name = getattr(annotation, "__name__", None) or getattr(
            annotation, "__forward_arg__", None
        )
        if isinstance(name, str) and name in known_names:
            out.add(name)
        return out

    for arg in args:
        out |= _referenced_type_names(arg, known_names)

    return out


def _build_composition_graph(
    class_map: dict[str, tuple[type, str, str]],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Return (uses, used_by) by class name."""
    from pydantic import BaseModel

    known_names = {cls.__name__ for _, (cls, _, _) in class_map.items()}
    uses: dict[str, set[str]] = defaultdict(set)
    used_by: dict[str, set[str]] = defaultdict(set)

    for qname, (cls, _, _) in class_map.items():
        if not (
            isinstance(cls, type)
            and issubclass(cls, BaseModel)
            and cls is not BaseModel
        ):
            continue
        try:
            fields = cls.model_fields
        except Exception:
            continue
        for field in fields.values():
            for ref in _referenced_type_names(field.annotation, known_names):
                if ref == cls.__name__:
                    continue
                uses[cls.__name__].add(ref)
                used_by[ref].add(cls.__name__)

    return uses, used_by


def _write_class_page(
    section_slug: str,
    module_name: str,
    class_name: str,
    uses: set[str],
    used_by: set[str],
    name_to_relpath: dict[str, str],
) -> Path:
    path = Path("reference") / section_slug / f"{class_name}.md"
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(f"# `{class_name}`\n\n")
        f.write(f"::: {module_name}.{class_name}\n\n")

        uses_list = sorted(uses)
        used_by_list = sorted(used_by)
        if uses_list or used_by_list:
            f.write("## Related types\n\n")
            if uses_list:
                f.write(
                    "**Uses:** "
                    + ", ".join(
                        f"[`{n}`]({_link(name_to_relpath, n)})" for n in uses_list
                    )
                    + "\n\n"
                )
            if used_by_list:
                f.write(
                    "**Used by:** "
                    + ", ".join(
                        f"[`{n}`]({_link(name_to_relpath, n)})" for n in used_by_list
                    )
                    + "\n\n"
                )

    return path


def _link(name_to_relpath: dict[str, str], name: str) -> str:
    relpath = name_to_relpath.get(name)
    if not relpath:
        return "#"
    return "../" + relpath


def _write_section_index(section: str, pages: list[tuple[str, Path]]) -> Path:
    section_slug = _slug(section)
    index_path = Path("reference") / section_slug / "index.md"
    with mkdocs_gen_files.open(index_path, "w") as f:
        f.write(f"# {section}\n\n")
        intro = SECTION_INTROS.get(section)
        if intro:
            f.write(intro + "\n\n")
        for name, page in pages:
            f.write(f"- [`{name}`]({page.name})\n")
    return index_path


def _write_summary(section_pages: list[tuple[str, list[tuple[str, Path]]]]) -> None:
    with mkdocs_gen_files.open(Path("reference") / "SUMMARY.md", "w") as f:
        f.write("- [Overview](index.md)\n")
        for section, pages in section_pages:
            section_slug = _slug(section)
            f.write(f"- {section}\n")
            f.write(f"    - [Overview]({section_slug}/index.md)\n")
            for name, page in pages:
                f.write(f"    - [{name}]({section_slug}/{page.name})\n")


def _write_overview(section_pages: list[tuple[str, list[tuple[str, Path]]]]) -> None:
    with mkdocs_gen_files.open(Path("reference") / "index.md", "w") as f:
        f.write("# Python SDK — API Reference\n\n")
        f.write(
            "Auto-generated reference for every public class in `playerdatapy`. "
            "Pages are rendered from source at build time, so they always match the installed package.\n\n"
        )
        f.write(
            "Browse by section in the left navigation. Each class page lists the **Related types** it uses and the ones that use it.\n\n"
        )
        for section, _ in section_pages:
            section_slug = _slug(section)
            intro = SECTION_INTROS.get(section, "")
            f.write(f"- **[{section}]({section_slug}/index.md)** — {intro}\n")


def main() -> None:
    class_map: dict[str, tuple[type, str, str]] = {}
    pending: list[tuple[str, str, list[tuple[str, type]]]] = []

    for section, modules in SECTIONS:
        section_slug = _slug(section)
        for module_name in modules:
            try:
                module = importlib.import_module(module_name)
            except Exception as exc:
                print(f"[gen_ref] skipping {module_name}: {exc}")
                continue
            classes = _public_classes(module)
            pending.append((section, module_name, classes))
            for class_name, cls in classes:
                page_name = f"{class_name}.md"
                class_map[f"{module_name}.{class_name}"] = (
                    cls,
                    section_slug,
                    page_name,
                )

    uses, used_by = _build_composition_graph(class_map)

    name_to_relpath: dict[str, str] = {
        cls.__name__: f"{section_slug}/{page_name}"
        for _, (cls, section_slug, page_name) in class_map.items()
    }

    all_section_pages: list[tuple[str, list[tuple[str, Path]]]] = []
    seen_sections: dict[str, list[tuple[str, Path]]] = defaultdict(list)

    for section, module_name, classes in pending:
        section_slug = _slug(section)
        for class_name, _ in classes:
            page = _write_class_page(
                section_slug=section_slug,
                module_name=module_name,
                class_name=class_name,
                uses=uses.get(class_name, set()),
                used_by=used_by.get(class_name, set()),
                name_to_relpath=name_to_relpath,
            )
            seen_sections[section].append((class_name, page))

    for section, _modules in SECTIONS:
        if section in seen_sections:
            pages = seen_sections[section]
            _write_section_index(section, pages)
            all_section_pages.append((section, pages))

    _write_overview(all_section_pages)
    _write_summary(all_section_pages)


main()
