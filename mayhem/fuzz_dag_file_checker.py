#!/usr/bin/env python3
# DAG source static analysis the dag-processor runs on every DAG file without executing it:
# check_dag_file_stability (AST visitors) and iter_airflow_imports. The input is written to a fresh
# temp .py under $TMPDIR and removed afterwards; it is parsed, never executed.
import os
import sys
import tempfile
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow.utils.dag_version_inflation_checker import check_dag_file_stability
    from airflow.utils.file import iter_airflow_imports

EXPECTED = (SyntaxError, ValueError, RecursionError, MemoryError)


def TestOneInput(data):
    fd, path = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        for fn in (check_dag_file_stability, lambda p: list(iter_airflow_imports(p))):
            try:
                fn(path)
            except EXPECTED:
                pass
    finally:
        os.unlink(path)


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
