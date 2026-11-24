#!/usr/bin/env python3
# Supervisor <-> task IPC. Responses go through the task side's own CommsDecoder._from_frame (msgspec
# _ResponseFrame decode, error frames -> AirflowRuntimeError, body -> TypeAdapter(ToTask)). Requests are
# decoded as _RequestFrame and validated against ToSupervisor, as the supervisor does; a request that
# validated is then re-framed with _RequestFrame.as_bytes() (the msgpack enc_hook) and must decode and
# validate again — the supervisor relies on that round trip.
import sys
import socket
import types
import af_common  # noqa: F401
import atheris

with atheris.instrument_imports(include=["airflow"], enable_loader_override=False):
    import msgspec
    import pydantic
    from airflow.sdk.exceptions import AirflowRuntimeError
    from airflow.sdk.execution_time import comms

_SOCK, _PEER = socket.socketpair()
# A silent logger: _from_frame logs every rejected body with a traceback before re-raising it.
_QUIET = types.SimpleNamespace(exception=lambda *a, **k: None, debug=lambda *a, **k: None)
DECODER = comms.CommsDecoder(socket=_SOCK, log=_QUIET)
REQ = msgspec.msgpack.Decoder(comms._RequestFrame)
TO_SUP = pydantic.TypeAdapter(comms.ToSupervisor)
EXPECTED = (msgspec.DecodeError, msgspec.ValidationError, pydantic.ValidationError, AirflowRuntimeError,
            ValueError, TypeError)


def TestOneInput(data):
    if not data:
        return -1
    payload = data[1:]
    if data[0] & 1:
        try:
            DECODER._from_frame(DECODER.resp_decoder.decode(payload))
        except EXPECTED:
            return
        return
    try:
        frame = REQ.decode(payload)
        if frame.body is None:
            return
        msg = TO_SUP.validate_python(frame.body)
    except EXPECTED:
        return
    again = comms._RequestFrame(id=frame.id, body=msg.model_dump()).as_bytes()
    TO_SUP.validate_python(REQ.decode(bytes(again[4:])).body)


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
