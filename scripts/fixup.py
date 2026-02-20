def add_import_line(path: str, import_line: str):
    with open(path, "r+") as f:
        content = f.read()
        content = import_line + content
        f.write(content)


def replace_import_line(path: str, import_line: str, new_import_line: str):
    with open(path, "r+") as f:
        content = f.read()
        content = content.replace(import_line, new_import_line)
        f.write(content)


def add_playerdata_api_to_init(path: str = "playerdatapy/__init__.py"):
    with open(path, "r") as f:
        content = f.read()

    import_line = "from .playerdata_api import PlayerDataAPI\n"
    if import_line not in content:
        content = content.replace(
            "__all__ = [", import_line + "\n__all__ = ["
        )

    if '"PlayerDataAPI"' not in content:
        content = content.replace(
            '__all__ = [', '__all__ = [\n    "PlayerDataAPI",'
        )

    with open(path, "w") as f:
        f.write(content)


def fixup():
    """
    Fix all the things that codegen breaks.
    """
    add_playerdata_api_to_init()

    import_line = "from playerdatapy.enums import *\n"
    for path in [
        "playerdatapy/custom_queries.py",
        "playerdatapy/custom_fields.py",
        "playerdatapy/custom_mutations.py",
    ]:
        add_import_line(path, import_line)

    optional_import_line = "from typing import Any, Union, Optional\n"
    previous_import_line = "from typing import Any, Union\n"
    path = "playerdatapy/custom_fields.py"
    replace_import_line(path, previous_import_line, optional_import_line)


if __name__ == "__main__":
    fixup()
