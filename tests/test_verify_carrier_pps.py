#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys

from blake3 import blake3
import jcs
from nacl.signing import SigningKey

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import verify_carrier_pps as verifier  # noqa: E402


def _jcs_bytes(obj):
    if hasattr(jcs, "canonicalize"):
        out = jcs.canonicalize(obj)
        return bytes(out) if isinstance(out, (bytes, bytearray)) else str(out).encode("utf-8")
    out = jcs.dumps(obj)
    return out.encode("utf-8") if isinstance(out, str) else bytes(out)


def signed_envelope():
    body = {
        "type": "pps.carrier.test",
        "time": "2026-05-31T00:00:00Z",
        "payload": {"message": "hello", "count": 1},
        "dryRun": True,
    }
    signing_key = SigningKey.generate()
    digest = blake3(_jcs_bytes(body)).digest()
    signature = signing_key.sign(digest).signature
    return {
        **body,
        "sig": signature.hex(),
        "pub": signing_key.verify_key.encode().hex(),
    }


def test_valid_envelope_verifies():
    assert verifier.verify_envelope(signed_envelope()) is True


def test_tampered_payload_fails():
    envelope = signed_envelope()
    envelope["payload"]["count"] = 2
    try:
        verifier.verify_envelope(envelope)
    except Exception:
        return
    raise AssertionError("tampered carrier payload unexpectedly verified")


def test_missing_body_field_fails():
    envelope = signed_envelope()
    del envelope["dryRun"]
    try:
        verifier.verify_envelope(envelope)
    except verifier.CarrierVerificationError:
        return
    raise AssertionError("carrier with missing dryRun unexpectedly verified")
