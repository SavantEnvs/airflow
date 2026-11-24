#!/usr/bin/env python3
# .airflowignore files (glob and regexp syntax): find_path_from_directory over a small fixed tree.
# The tree is created once and never modified; the ignore file is rewritten for every input.
import os
import re
import sys
import tempfile
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow._shared.module_loading.file_discovery import find_path_from_directory

BASE = tempfile.mkdtemp(prefix="airflowignore-")
for rel in ("a.py", "b/c.py", "b/d/e.py", "f/g.txt", ".hidden/h.py", "b/.airflowignore"):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write("# x\n" if not rel.endswith(".airflowignore") else "d/\n")
IGNORE = os.path.join(BASE, ".airflowignore")
EXPECTED = (re.error, ValueError, RecursionError)


def TestOneInput(data):
    if not data:
        return -1
    syntax = "regexp" if data[0] & 1 else "glob"
    with open(IGNORE, "wb") as f:
        f.write(data[1:])
    try:
        list(find_path_from_directory(BASE, ".airflowignore", syntax))
    except EXPECTED:
        return
    except UnicodeDecodeError:
        return -1


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
