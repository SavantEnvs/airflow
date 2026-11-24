#!/usr/bin/env python3
# Port of OSS-Fuzz projects/airflow/dag_fuzz.py, fixed for Airflow 3: `schedule_interval=` was
# removed (it raised TypeError, which the old harness swallowed, so every input was a no-op). The
# fuzzer now also picks the schedule string (cron / preset / timedelta-ish), which DAG() parses into
# a timetable, and the DAG is serialized so the serializer runs over the fuzzed attributes.
import sys
import af_common  # noqa: F401  (sys.path + AIRFLOW_HOME)
import atheris
from datetime import datetime, timedelta

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow.sdk import DAG
    from airflow.sdk.exceptions import AirflowException
    from airflow.providers.standard.operators.empty import EmptyOperator
    from airflow.providers.standard.operators.python import PythonOperator
    from airflow.serialization.serialized_objects import DagSerialization

    try:
        from airflow.exceptions import AirflowException as CoreAirflowException
    except ImportError:  # pragma: no cover
        CoreAirflowException = AirflowException

EXPECTED = (AirflowException, CoreAirflowException, ValueError, KeyError)
PRESETS = ["@daily", "@hourly", "@once", "@continuous", "@weekly", None]


def py_func():
    return


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    default_args = {
        "owner": fdp.ConsumeUnicodeNoSurrogates(8),
        "depends_on_past": fdp.ConsumeBool(),
        "start_date": datetime(2024, 1, 1) - timedelta(days=fdp.ConsumeIntInRange(1, 5)),
        "email": [fdp.ConsumeUnicodeNoSurrogates(8)],
        "email_on_failure": fdp.ConsumeBool(),
        "email_on_retry": fdp.ConsumeBool(),
        "retries": fdp.ConsumeIntInRange(1, 5),
        "retry_delay": timedelta(minutes=fdp.ConsumeIntInRange(1, 5)),
    }
    if fdp.ConsumeBool():
        schedule = PRESETS[fdp.ConsumeIntInRange(0, len(PRESETS) - 1)]
    else:
        schedule = fdp.ConsumeUnicodeNoSurrogates(32)
    dag_id = fdp.ConsumeUnicodeNoSurrogates(16)
    t1 = fdp.ConsumeUnicodeNoSurrogates(12)
    t2 = fdp.ConsumeUnicodeNoSurrogates(12)
    try:
        with DAG(dag_id, schedule=schedule, default_args=default_args) as dag:
            dummy_task = EmptyOperator(task_id=t1, retries=fdp.ConsumeIntInRange(1, 5))
            python_task = PythonOperator(task_id=t2, python_callable=py_func)
            dummy_task >> python_task
        DagSerialization.to_dict(dag)
    except EXPECTED:
        return


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
