#!/usr/bin/env python3
# airflow.cfg text: AirflowConfigParser.read_string plus the typed getters over every option.
# A fresh parser per input, so no state leaks between inputs.
import sys
import configparser
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow.configuration import AirflowConfigParser
    from airflow._shared.configuration.exceptions import AirflowConfigException

EXPECTED = (configparser.Error, AirflowConfigException, ValueError, KeyError)


def TestOneInput(data):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return -1
    p = AirflowConfigParser()
    try:
        p.read_string(text)
        for section in p.sections():
            for option in p.options(section):
                for getter in (p.get, p.getboolean, p.getint, p.getfloat, p.getlist, p.getjson):
                    try:
                        getter(section, option)
                    except EXPECTED:
                        pass
        p.as_dict(display_source=True, raw=False)
    except EXPECTED:
        return


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
