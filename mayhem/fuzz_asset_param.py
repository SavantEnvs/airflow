#!/usr/bin/env python3
# Asset URIs (scheme normalisation / validation) and Param JSON-schema validation:
# Asset(uri=...), Asset(name=..., uri=...), Param(value, **schema).resolve().
import json
import sys
import af_common  # noqa: F401
import atheris
import jsonschema

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow.sdk import Asset, Param
    from airflow.sdk.exceptions import ParamValidationError, AirflowException

# SchemaError: Param() rejects a user schema that is not itself a valid JSON schema.
EXPECTED = (jsonschema.exceptions.SchemaError, ValueError, TypeError, KeyError, ParamValidationError, AirflowException)


def TestOneInput(data):
    if not data:
        return -1
    mode = data[0] % 3
    try:
        text = data[1:].decode("utf-8")
    except UnicodeDecodeError:
        return -1
    try:
        if mode == 0:
            Asset(uri=text)
        elif mode == 1:
            name, _, uri = text.partition("\n")
            Asset(name=name, uri=uri)
        else:
            try:
                obj = json.loads(text)
            except (ValueError, RecursionError):
                return -1
            if not isinstance(obj, dict) or "value" not in obj:
                return -1
            value = obj.pop("value")
            schema = obj.get("schema", {})
            if not isinstance(schema, dict):
                return -1
            Param(value, **{str(k): v for k, v in schema.items()}).resolve()
    except EXPECTED:
        return


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
