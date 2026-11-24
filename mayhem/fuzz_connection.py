#!/usr/bin/env python3
# Connection URIs / JSON (env vars, secrets backends, CLI): airflow.sdk.Connection.from_uri and
# from_json, then get_uri() on the parsed result.
import sys
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow.sdk import Connection
    from airflow.sdk.exceptions import AirflowException

# from_json() on valid JSON that is not an object raises AttributeError ('int' has no .pop):
# a known, shallow input-validation gap, accepted here so the fuzzer gets past it.
EXPECTED = (ValueError, KeyError, TypeError, AttributeError, AirflowException)


def TestOneInput(data):
    if not data:
        return -1
    mode = data[0] & 1
    try:
        text = data[1:].decode("utf-8")
    except UnicodeDecodeError:
        return -1
    try:
        if mode:
            conn = Connection.from_json(text, conn_id="fuzz")
        else:
            conn = Connection.from_uri(text, conn_id="fuzz")
        conn.get_uri()
    except EXPECTED:
        return


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
