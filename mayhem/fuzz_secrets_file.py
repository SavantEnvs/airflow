#!/usr/bin/env python3
# Local-filesystem secrets backend files (.env / .yaml / .json): load_connections_dict and
# load_variables. The input is written to a fresh temp file under $TMPDIR, removed afterwards.
import os
import sys
import tempfile
import af_common  # noqa: F401
import atheris
import yaml

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow.secrets.local_filesystem import load_connections_dict, load_variables
    from airflow.exceptions import AirflowException
    from airflow.sdk.exceptions import AirflowException as SdkAirflowException

EXPECTED = (yaml.YAMLError, AirflowException, SdkAirflowException, ValueError, KeyError, TypeError)
SUFFIXES = [".env", ".yaml", ".json"]


def TestOneInput(data):
    if not data:
        return -1
    suffix = SUFFIXES[data[0] % 3]
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data[1:])
        for fn in (load_connections_dict, load_variables):
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
