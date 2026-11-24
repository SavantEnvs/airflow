#!/usr/bin/env python3
# Public REST API (core_api) request bodies (the *Body models) and every Task Execution API model under
# airflow.api_fastapi.{core_api,execution_api}.datamodels, with their custom validators. The first two
# bytes pick the model; the rest is the JSON body handed to model_validate_json, as FastAPI does.
import sys
import importlib
import pkgutil
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    import pydantic
    import airflow.api_fastapi.core_api.datamodels as core_dm
    import airflow.api_fastapi.execution_api.datamodels as exec_dm
    MODELS = None  # filled below, inside the instrumentation scope


def _models():
    found = {}
    for pkg in (core_dm, exec_dm):
        for info in pkgutil.iter_modules(pkg.__path__):
            if info.ispkg:
                continue
            try:
                mod = importlib.import_module(f"{pkg.__name__}.{info.name}")
            except Exception:
                continue
            for name in sorted(vars(mod)):
                obj = getattr(mod, name)
                # core_api: request bodies only (its *Response models are server-built, trusted);
                # execution_api: every model (workers send them, the SDK client parses replies).
                if (isinstance(obj, type) and issubclass(obj, pydantic.BaseModel)
                        and obj.__module__ == mod.__name__
                        and (pkg is exec_dm or name.endswith("Body"))):
                    found[f"{obj.__module__}.{name}"] = obj
    return [found[k] for k in sorted(found)]


with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    MODELS = _models()
EXPECTED = (pydantic.ValidationError, ValueError, TypeError)


def TestOneInput(data):
    if len(data) < 2:
        return -1
    model = MODELS[int.from_bytes(data[:2], "big") % len(MODELS)]
    try:
        model.model_validate_json(data[2:])
    except EXPECTED:
        return


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
