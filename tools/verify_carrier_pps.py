#!/usr/bin/env python3
"""Verify PPS-aligned A2A/MCP carrier envelopes.

CarrierBody canonicalization follows RFC 8785 JSON Canonicalization Scheme (JCS).
The verifier computes BLAKE3-256 over the canonical body and verifies an Ed25519
signature over that 32-byte digest.

Expected envelope shape:

{
  "type": "...",
  "time": "...",
  "payload": {...},
  "dryRun": true,
  "sig": "<hex Ed25519 signature over BLAKE3(canonical body)>",
  "pub": "<hex Ed25519 verify key>"
}

Only these body fields are signed: type, time, payload, dryRun.
"""
from __future__ import annotations

import argparse
import binascii
import json
import os
import sys
from typing import Any

from blake3 import blake3
import jcs
from nacl.signing import VerifyKey

SIGNED_BODY_FIELDS = ("type", "time", "payload", "dryRun")
SIGNATURE_FIELDS = ("sig", "pub")


class CarrierVerificationError(ValueError):
    """Raised when a carrier envelope is malformed or fails verification."""


def jcs_bytes(obj: Any) -> bytes:
    """Return RFC 8785/JCS canonical bytes using either supported jcs API."""
    if hasattr(jcs, "canonicalize"):
        out = jcs.canonicalize(obj)
        return bytes(out) if isinstance(out, (bytes, bytearray)) else str(out).encode("utf-8")
    if hasattr(jcs, "dumps"):
        out = jcs.dumps(obj)
        return out.encode("utf-8") if isinstance(out, str) else bytes(out)
    raise RuntimeError("Unsupported jcs API; expected canonicalize() or dumps().")


def carrier_body(envelope: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in SIGNED_BODY_FIELDS if field not in envelope]
    if missing:
        raise CarrierVerificationError(f"missing signed body fields: {missing}")
    return {field: envelope[field] for field in SIGNED_BODY_FIELDS}


def carrier_digest(envelope: dict[str, Any]) -> bytes:
    return blake3(jcs_bytes(carrier_body(envelope))).digest()


def verify_envelope(envelope: dict[str, Any]) -> bool:
    missing = [field for field in SIGNATURE_FIELDS if field not in envelope]
    if missing:
        raise CarrierVerificationError(f"missing signature fields: {missing}")
    try:
        signature = binascii.unhexlify(envelope["sig"])
        public_key = binascii.unhexlify(envelope["pub"])
    except (TypeError, binascii.Error) as exc:
        raise CarrierVerificationError(f"invalid hex signature field: {exc}") from exc
    VerifyKey(public_key).verify(carrier_digest(envelope), signature)
    return True


def verify_file(path: str) -> bool:
    with open(path, "r", encoding="utf-8") as handle:
        envelope = json.load(handle)
    if not isinstance(envelope, dict):
        raise CarrierVerificationError("carrier envelope must be a JSON object")
    return verify_envelope(envelope)


def iter_json_files(path: str) -> list[str]:
    if os.path.isfile(path):
        return [path] if path.endswith(".json") else []
    if os.path.isdir(path):
        return [os.path.join(path, name) for name in sorted(os.listdir(path)) if name.endswith(".json")]
    raise FileNotFoundError(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="out/carriers", help="carrier JSON file or directory")
    args = parser.parse_args()

    try:
        files = iter_json_files(args.path)
    except FileNotFoundError:
        print(json.dumps({"error": f"path not found: {args.path}"}), file=sys.stderr)
        return 2

    verified = 0
    failed = 0
    for path in files:
        try:
            verify_file(path)
            verified += 1
        except Exception as exc:
            failed += 1
            print(json.dumps({"file": path, "error": str(exc)}), file=sys.stderr)

    print(json.dumps({"verified": verified, "failed": failed}))
    return 0 if failed == 0 and verified > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
