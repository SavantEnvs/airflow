#!/usr/bin/env python3
# Client-supplied REST pagination cursors: parse_cursor (the "~" backward prefix) and decode_cursor
# (padded base64url + msgpack list) from airflow.api_fastapi.common.cursors.
import sys
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from fastapi import HTTPException
    from airflow.api_fastapi.common import cursors


def TestOneInput(data):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return -1
    token, _backward = cursors.parse_cursor(text)
    try:
        values = cursors.decode_cursor(token)
    except HTTPException:
        return
    if not isinstance(values, list):
        raise AssertionError(f"decode_cursor returned {type(values)!r}")


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
