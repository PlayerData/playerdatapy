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


def fix_imports():
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
    fix_imports()
