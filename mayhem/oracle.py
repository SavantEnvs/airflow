#!/usr/bin/env python3
"""Known-answer self-test over the harnessed parsers (run by mayhem/test.sh via mayhem/airflow_oracle).

Each check asserts a concrete value; the PASS lines are printed only when it holds."""
import datetime
import json
import sys
import tempfile
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import af_common  # noqa: F401,E402

passed = failed = 0


def check(name, fn):
    global passed, failed
    try:
        got = fn()
        print(f"PASS {name} {got}")
        passed += 1
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {name}: {type(e).__name__}: {e}")
        failed += 1


def t_connection():
    from airflow.sdk import Connection
    c = Connection.from_uri("postgres://user:p%40ss@db.example.com:5432/airdb?sslmode=require", conn_id="c")
    assert (c.conn_type, c.host, c.login, c.password, c.port, c.schema) == (
        "postgres", "db.example.com", "user", "p@ss", 5432, "airdb"), vars(c)
    assert c.extra_dejson == {"sslmode": "require"}, c.extra_dejson
    return f"host={c.host} port={c.port}"


def t_base_serialization():
    from airflow.serialization.serialized_objects import BaseSerialization
    v = BaseSerialization.from_json('{"__type":"dict","__var":{"a":{"__type":"timedelta","__var":90.0},"b":{"__type":"set","__var":[1,2]}}}')
    assert v == {"a": datetime.timedelta(seconds=90), "b": {1, 2}}, v
    return "timedelta=90s"


def t_dag_roundtrip():
    from airflow.sdk import DAG
    from airflow.providers.standard.operators.empty import EmptyOperator
    from airflow.serialization.serialized_objects import DagSerialization
    with DAG("oracle_dag", schedule="@daily", start_date=datetime.datetime(2024, 1, 1)) as dag:
        EmptyOperator(task_id="a") >> EmptyOperator(task_id="b")
    d = json.loads(json.dumps(DagSerialization.to_dict(dag)))
    sd = DagSerialization.from_dict(d)
    assert sd.dag_id == "oracle_dag" and sorted(sd.task_dict) == ["a", "b"], (sd.dag_id, sd.task_dict)
    assert sd.task_dict["a"].downstream_task_ids == {"b"}
    return "tasks=a,b"


def t_serde():
    from airflow.sdk import serde
    v = serde.deserialize(serde.serialize((1, "x", datetime.timedelta(seconds=5))))
    assert v == (1, "x", datetime.timedelta(seconds=5)), v
    return "tuple"


def t_cron():
    from airflow.timetables.interval import CronDataIntervalTimetable
    from airflow.timetables.base import TimeRestriction
    from airflow._shared.timezones import timezone
    tt = CronDataIntervalTimetable("30 6 * * *", timezone=timezone.parse_timezone("UTC"))
    start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    info = tt.next_dagrun_info(last_automated_data_interval=None,
                               restriction=TimeRestriction(earliest=start, latest=None, catchup=True))
    assert info.data_interval.start.isoformat() == "2024-01-01T06:30:00+00:00", info
    assert info.data_interval.end.isoformat() == "2024-01-02T06:30:00+00:00", info
    return "start=2024-01-01T06:30"


def t_config():
    from airflow.configuration import AirflowConfigParser
    p = AirflowConfigParser()
    p.read_string("[core]\nparallelism = 17\nflag = True\nitems = a,b,c\n")
    assert p.getint("core", "parallelism") == 17
    assert p.getboolean("core", "flag") is True
    return "parallelism=17"


def t_secrets_file():
    from airflow.secrets.local_filesystem import load_variables
    fd, path = tempfile.mkstemp(suffix=".env")
    with os.fdopen(fd, "w") as f:
        f.write("KEY_A=value_a\nKEY_B=42\n")
    try:
        v = load_variables(path)
    finally:
        os.unlink(path)
    assert v == {"KEY_A": "value_a", "KEY_B": "42"}, v
    return "vars=2"


for n, f in [("connection", t_connection), ("base_serialization", t_base_serialization),
             ("dag_roundtrip", t_dag_roundtrip), ("serde", t_serde), ("cron", t_cron),
             ("config", t_config), ("secrets_file", t_secrets_file)]:
    check(n, f)
print(f"ORACLE passed={passed} failed={failed}")
sys.exit(1 if failed else 0)
