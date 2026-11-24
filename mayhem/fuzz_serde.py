#!/usr/bin/env python3
# XCom values: airflow.sdk.serde.deserialize (__classname__ / __version__ / __data__, the
# allowed-class checks, the per-type serializers) in both full and stringify (full=False) modes.
import sys
import json
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow.sdk import serde

EXPECTED = (ValueError, KeyError, TypeError, ImportError)


def TestOneInput(data):
    if not data:
        return -1
    full = bool(data[0] & 1)
    try:
        obj = json.loads(data[1:].decode("utf-8", "surrogatepass"))
    except (ValueError, UnicodeDecodeError, RecursionError):
        return -1
    try:
        serde.deserialize(obj, full=full)
    except EXPECTED:
        return


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
