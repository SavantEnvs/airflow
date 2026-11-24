#!/usr/bin/env python3
# Generic {"__type": ..., "__var": ...} decoder: BaseSerialization.from_json (timedelta, datetime,
# timezone, set/tuple/dict, assets, params, connections, exceptions, ...).
import sys
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow.serialization.serialized_objects import BaseSerialization
    from airflow.exceptions import AirflowException, SerializationError, DeserializationError
    from airflow.sdk.exceptions import AirflowException as SdkAirflowException

# RuntimeError: the POD decoder raises it when the optional kubernetes package is absent (not installed here).
EXPECTED = (RuntimeError, ValueError, KeyError, TypeError, AirflowException, SdkAirflowException, SerializationError, DeserializationError)


def TestOneInput(data):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return -1
    try:
        BaseSerialization.from_json(text)
    except EXPECTED:
        return


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
