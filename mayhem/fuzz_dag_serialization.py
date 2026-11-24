#!/usr/bin/env python3
# Serialized-DAG JSON (what the scheduler/API server read back from the metadata DB):
# json -> DagSerialization.from_dict (schema validation + every decoder in serialized_objects.py).
import sys
import json
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow.serialization.serialized_objects import DagSerialization
    from airflow.exceptions import AirflowException, SerializationError, DeserializationError
    from airflow.sdk.exceptions import AirflowException as SdkAirflowException

# RuntimeError: the POD decoder raises it when the optional kubernetes package is absent (not installed here).
EXPECTED = (RuntimeError, ValueError, KeyError, TypeError, AirflowException, SdkAirflowException, SerializationError, DeserializationError)


def TestOneInput(data):
    try:
        obj = json.loads(data.decode("utf-8", "surrogatepass"))
    except (ValueError, UnicodeDecodeError, RecursionError):
        return -1
    if not isinstance(obj, dict):
        return -1
    try:
        DagSerialization.from_dict(obj)
    except EXPECTED:
        return


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
