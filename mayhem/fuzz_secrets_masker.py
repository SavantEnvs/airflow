#!/usr/bin/env python3
# Secret redaction: SecretsMasker.add_mask (string / dict secrets, regex replacer build) and the
# recursive redact() walk over a JSON structure. Invariant: a registered secret of >= 5 printable
# chars never survives redaction of a plain string that contains it.
import sys
import json
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    from airflow._shared.secrets_masker.secrets_masker import SecretsMasker


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    m = SecretsMasker()
    secrets = [fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 24)) for _ in range(fdp.ConsumeIntInRange(0, 3))]
    for s in secrets:
        m.add_mask(s)
    key = fdp.ConsumeUnicodeNoSurrogates(12)
    rest = fdp.ConsumeUnicodeNoSurrogates(fdp.remaining_bytes())
    try:
        obj = json.loads(rest)
    except (ValueError, RecursionError):
        obj = rest
    try:
        m.redact(obj, name=key or None)
    except RecursionError:
        return
    for s in secrets:
        if len(s) >= 5 and s.isprintable() and s.strip() == s:
            out = m.redact("x " + s + " y")
            if s in out:
                raise AssertionError(f"secret {s!r} not masked: {out!r}")


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
