#!/usr/bin/env python3
# Date/time and timezone strings: airflow._shared.timezones timezone.parse / parse_timezone and the
# RFC 3339 / ISO 8601 validators used by the serialized-DAG JSON schema.
import sys
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow._shared.timezones import timezone, rfc3339
    import pendulum.parsing.exceptions as pexc

EXPECTED = (ValueError, pexc.ParserError, OverflowError)


def TestOneInput(data):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return -1
    rfc3339.is_rfc3339_datetime(text)
    rfc3339.is_iso8601_datetime(text)
    for fn in (timezone.parse, timezone.parse_timezone):
        try:
            fn(text)
        except EXPECTED:
            pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
