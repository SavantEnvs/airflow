#!/usr/bin/env python3
# Bearer tokens: JWTValidator.avalidated_claims with a fixed HS512 secret, issuer and audience
# (header/claims parsing, required exp/iat/nbf, issuer/audience checks, extra required claims).
import sys
import asyncio
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    import jwt
    from airflow.api_fastapi.auth.tokens import JWTValidator

VALIDATOR = JWTValidator(secret_key="mayhem-fuzz-hs512-secret-key-0123456789abcdef0123456789abcdef0123", issuer="mayhem",
                         audience="urn:airflow.apache.org:task", algorithm=["HS512"], leeway=0)
LOOP = asyncio.new_event_loop()
EXPECTED = (jwt.InvalidTokenError, ValueError, TypeError)


def TestOneInput(data):
    if not data:
        return -1
    try:
        token = data[1:].decode("utf-8")
    except UnicodeDecodeError:
        return -1
    required = {"sub": "ti"} if data[0] & 1 else None
    try:
        LOOP.run_until_complete(VALIDATOR.avalidated_claims(token, required))
    except EXPECTED:
        return


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
