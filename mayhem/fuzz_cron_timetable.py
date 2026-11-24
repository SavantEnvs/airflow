#!/usr/bin/env python3
# Cron schedule strings: CronDataIntervalTimetable / CronTriggerTimetable validation, description
# and next-run computation.
import sys
import af_common  # noqa: F401
import atheris
import datetime

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow.timetables.interval import CronDataIntervalTimetable
    from airflow.timetables.trigger import CronTriggerTimetable
    from airflow.timetables.base import TimeRestriction
    from airflow.exceptions import AirflowTimetableInvalid
    from airflow._shared.timezones import timezone

EXPECTED = (ValueError, KeyError, AirflowTimetableInvalid, OverflowError)
TZS = ["UTC", "Europe/Amsterdam", "America/New_York", "Asia/Kolkata"]
START = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)


def TestOneInput(data):
    if len(data) < 2:
        return -1
    tz = TZS[data[0] % len(TZS)]
    trigger = bool(data[1] & 1)
    try:
        cron = data[2:].decode("utf-8")
    except UnicodeDecodeError:
        return -1
    try:
        if trigger:
            tt = CronTriggerTimetable(cron, timezone=timezone.parse_timezone(tz))
        else:
            tt = CronDataIntervalTimetable(cron, timezone=timezone.parse_timezone(tz))
        tt.validate()
        _ = tt.summary
        _ = tt.description
        tt.next_dagrun_info(
            last_automated_data_interval=None,
            restriction=TimeRestriction(earliest=START, latest=None, catchup=True),
        )
    except EXPECTED:
        return


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
