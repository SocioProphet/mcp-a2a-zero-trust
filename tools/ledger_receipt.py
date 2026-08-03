#!/usr/bin/env python3
"""Native, hash-chained LedgerEvent emission for governed A2A / MCP actions (T7-17).

Tranche-7 downstream. The estate receipt spine is already live in two places:

  * the model-plane **InferenceReceipt** (prophet-platform receipt-gateway, #1233/#1237) —
    receipts every model completion; and
  * the **ProofArtifact** knowledge-publish arm (prophet-workspace tools/proof-artifact-spine,
    ADR-0001 WO-B) behind the `Ledger.Push` triRPC verb.

Both use one discipline: canonical JSON (sorted keys, compact) + sha256 + a per-entry
`ledgerPrevHash`/`prev_hash` link, so the ledger is append-only and tamper-evident.

This repository owns the zero-trust **authority** ledger (`ledger/schema.json` — `LedgerEvent`).
The schema already *declares* the chaining fields (`payload_hash`, `policy_hash`, `prev_hash`,
`hash`) and an optional binding to the model-plane receipt via
`evidence_refs.event_ir_ref` / `event_ir_hash` (`RuntimeEvidenceRefs`). What was missing:

  1. nothing *computed* the chain natively (the hashes were free-form 64-hex placeholders); and
  2. nothing *enforced* that a governed inference/tool dispatch carries its InferenceReceipt
     binding — so an agent-to-agent tool call could be logged while **bypassing the spine**.

This module closes both. `emit_ledger_event()` writes a schema-conformant, hash-chained
`LedgerEvent` and, for tool/inference dispatch event types, is **fail-closed** on the receipt
binding (AC-1 — the receipt law: no receipt ⇒ no governed action). `verify_ledger()` independently
re-checks the whole chain and the binding law, so a hand-crafted event that skipped the emitter is
caught. The canonicalization is byte-compatible with `inference_receipt_emitter.py`, so the
`event_ir_hash` this module binds is exactly the content hash the model-plane ledger computes for
the same receipt — one shared spine, referenced not forked.

CLI: `ledger_receipt.py --selftest`   (0 ok; 1 conformance/chain failure; 2 usage/dep error)
     `ledger_receipt.py --verify <ledger.jsonl>`
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SCHEMA = ROOT / "ledger" / "schema.json"
EVIDENCE_SCHEMA = ROOT / "schemas" / "governance" / "runtime_evidence_refs.schema.json"

GENESIS_PREV = "sha256:" + "0" * 64  # the first entry chains to genesis

# Tool / inference dispatch events — the agent-to-agent inference/tool calls that must NOT bypass
# the model-plane receipt spine. Each of these MUST carry an InferenceReceipt binding
# (evidence_refs.event_ir_ref + event_ir_hash). Pure authority events (grants, hellos, approvals)
# do not invoke a model and are exempt.
INFERENCE_BEARING_TYPES = frozenset({"MCP_CALL", "MCP_RESULT", "OP_TOOL_INVOKE"})

# Fields excluded from the chained hash: `hash` is the output; `signatures` are applied over `hash`.
_HASH_EXCLUDED = ("hash", "signatures")


class LedgerEmissionError(Exception):
    """Raised when a governed action cannot be receipted. The caller MUST treat this as a failed
    action (AC-1): if no chained, spine-bound receipt can be written, nothing is governed."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def sha256(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()


def canonical(obj) -> str:
    """Deterministic JSON for hashing/chaining — byte-compatible with the estate receipt emitters
    (inference_receipt_emitter.py / proof_artifact.py): sorted keys, compact separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _entry_hash(prev_hash: str, event: dict) -> str:
    """Chain hash over the canonical event body (minus `hash`/`signatures`) bound to the prior link.
    Mirrors ProofArtifact's entryHash = sha256(prev_hash + canonical(body))."""
    body = {k: v for k, v in event.items() if k not in _HASH_EXCLUDED}
    return sha256(prev_hash + canonical(body))


def _last_entry(ledger: Path) -> dict | None:
    if not ledger.exists():
        return None
    last = None
    with ledger.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                last = json.loads(line)
    return last


def _event_ir_hash(inference_receipt: dict) -> str:
    """Content hash of a model-plane InferenceReceipt, computed exactly as the model-plane ledger
    would (sha256 over canonical JSON). This is the real cross-spine binding, not a placeholder."""
    return sha256(canonical(inference_receipt))


def emit_ledger_event(
    ledger: Path,
    *,
    event_type: str,
    actor: dict,
    payload: dict,
    policy: dict,
    target: dict | None = None,
    decision: dict | None = None,
    redaction: dict | None = None,
    grant_id: str | None = None,
    trust_boundary_id: str | None = None,
    authority_envelope_id: str | None = None,
    inference_receipt: dict | None = None,
    event_ir_ref: str | None = None,
    event_ir_hash: str | None = None,
    extra_evidence: dict | None = None,
    ts: str | None = None,
    event_id: str | None = None,
) -> dict:
    """Append one hash-chained, schema-shaped ``LedgerEvent`` and return it.

    For tool/inference dispatch events (``INFERENCE_BEARING_TYPES``) the model-plane receipt binding
    is **required** and this call is fail-closed (AC-1): supply either the ``inference_receipt`` dict
    (its content hash is computed and bound) or an explicit ``event_ir_ref`` + ``event_ir_hash``.
    Missing binding ⇒ ``LedgerEmissionError('receipt-required')`` and nothing is written.
    """
    ledger = Path(ledger)
    ts = ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1) resolve the model-plane receipt binding
    evidence: dict = dict(extra_evidence or {})
    if inference_receipt is not None:
        computed = _event_ir_hash(inference_receipt)
        if event_ir_hash is not None and event_ir_hash != computed:
            raise LedgerEmissionError(
                "receipt-hash-mismatch",
                f"event_ir_hash {event_ir_hash} != sha256(canonical(inference_receipt)) {computed}")
        event_ir_hash = computed
    if event_ir_ref is not None:
        evidence["event_ir_ref"] = event_ir_ref
    if event_ir_hash is not None:
        evidence["event_ir_hash"] = event_ir_hash

    # 2) the receipt law (AC-1) — tool/inference dispatch cannot bypass the spine
    if event_type in INFERENCE_BEARING_TYPES:
        if not evidence.get("event_ir_ref") or not evidence.get("event_ir_hash"):
            raise LedgerEmissionError(
                "receipt-required",
                f"{event_type} is an inference/tool dispatch and MUST bind an InferenceReceipt "
                "(evidence_refs.event_ir_ref + event_ir_hash); refusing to emit a spine-bypassing event")

    # 3) content hashes for payload + policy
    payload_hash = sha256(canonical(payload))
    policy_hash = sha256(canonical(policy))

    # 4) chain link
    prev = _last_entry(ledger)
    prev_hash = prev["hash"] if prev else GENESIS_PREV

    # 5) stable event_id (>= 8 chars); deterministic from content when not supplied
    if event_id is None:
        event_id = "evt_" + hashlib.sha256(
            (payload_hash + ts + event_type).encode("utf-8")).hexdigest()[:12]

    event: dict = {
        "event_id": event_id,
        "ts": ts,
        "type": event_type,
        "actor": actor,
        "payload_hash": payload_hash,
        "policy_hash": policy_hash,
        "prev_hash": prev_hash,
    }
    if target is not None:
        event["target"] = target
    if decision is not None:
        event["decision"] = decision
    if redaction is not None:
        event["redaction"] = redaction
    if grant_id is not None:
        event["grant_id"] = grant_id
    if trust_boundary_id is not None:
        event["trust_boundary_id"] = trust_boundary_id
    if authority_envelope_id is not None:
        event["authority_envelope_id"] = authority_envelope_id
    if evidence:
        event["evidence_refs"] = evidence

    # 6) seal + append (fail-closed: an action whose receipt cannot be written is not governed)
    event["hash"] = _entry_hash(prev_hash, event)
    try:
        with ledger.open("a", encoding="utf-8") as f:
            f.write(canonical(event) + "\n")
    except OSError as e:
        raise LedgerEmissionError("ledger-write-failed", f"ledger write failed: {e}") from e
    return event


def build_validator():
    """Draft2020-12 validator for LedgerEvent, with the RuntimeEvidenceRefs $ref resolved locally.
    Returns None if jsonschema/referencing are unavailable (chain checks still run)."""
    try:
        import jsonschema
        from referencing import Registry, Resource
    except Exception:
        return None
    ledger_schema = json.loads(LEDGER_SCHEMA.read_text(encoding="utf-8"))
    evidence_schema = json.loads(EVIDENCE_SCHEMA.read_text(encoding="utf-8"))
    pairs = [(evidence_schema["$id"], Resource.from_contents(evidence_schema))]
    sid = ledger_schema.get("$id")
    if sid:
        pairs.append((sid, Resource.from_contents(ledger_schema)))
    registry = Registry().with_resources(pairs)
    return jsonschema.Draft202012Validator(ledger_schema, registry=registry)


def verify_ledger(ledger: Path, validator=None) -> tuple[bool, str]:
    """Independently verify the whole chain — teeth both ways:

      * every entry is schema-conformant (when a validator is supplied);
      * ``prev_hash`` links (genesis → entry0 → entry1 → …) and each ``hash`` recomputes; and
      * every inference/tool dispatch event carries its InferenceReceipt binding — a governed
        action that skipped the emitter and bypassed the spine is caught here.
    """
    ledger = Path(ledger)
    if not ledger.exists():
        return True, "empty ledger"
    prev_hash = GENESIS_PREV
    n = 0
    with ledger.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                return False, f"entry {i} is not valid JSON: {e}"

            if validator is not None:
                errs = sorted(validator.iter_errors(entry), key=lambda e: list(e.path))
                if errs:
                    return False, f"entry {i} schema-invalid: {errs[0].message}"

            if entry.get("prev_hash") != prev_hash:
                return False, f"entry {i} chain broken: prev_hash != hash(entry {i - 1})"

            recomputed = _entry_hash(prev_hash, entry)
            if recomputed != entry.get("hash"):
                return False, f"entry {i} tamper: hash mismatch (recomputed {recomputed})"

            if entry.get("type") in INFERENCE_BEARING_TYPES:
                ev = entry.get("evidence_refs") or {}
                if not ev.get("event_ir_ref") or not ev.get("event_ir_hash"):
                    return False, (f"entry {i} spine-bypass: {entry.get('type')} lacks an "
                                   "InferenceReceipt binding (evidence_refs.event_ir_ref/hash)")

            prev_hash = entry["hash"]
            n += 1
    return True, f"chain valid ({n} entries): schema-conformant, hash-chained, spine-bound"


# --------------------------------------------------------------------------------------------------
# selftest — proves the emitter/verifier both ways without any live gateway or cluster creds.
# --------------------------------------------------------------------------------------------------
def _synthetic_inference_receipt(seq: int) -> dict:
    """A schema-shaped model-plane InferenceReceipt (as receipt-gateway would emit). SYNTHETIC —
    no model is run here; it exists only so we can bind a real content hash into the LedgerEvent."""
    return {
        "id": f"urn:srcos:inference-receipt:selftest-{seq}",
        "type": "InferenceReceipt",
        "specVersion": "2.1.0",
        "issuedAt": "2026-08-03T00:00:00Z",
        "providerDaemon": "inferenced",
        "tier": "T1",
        "baseModelDigest": "sha256:" + "a" * 64,
        "task": "selftest",
        "inputHash": sha256(f"prompt {seq}"),
        "outputHash": sha256(f"completion {seq}"),
        "dataResidencyClass": "on_device_only",
        "ledgerSeq": seq,
    }


def _selftest() -> int:
    import tempfile

    validator = build_validator()
    if validator is None:
        print("ERR: jsonschema/referencing not installed", file=sys.stderr)
        return 2

    actor = {"spiffe_id": "spiffe://sourceos/inception"}
    ok_all = True

    def say(ok: bool, name: str, detail: str = "") -> None:
        nonlocal ok_all
        ok_all = ok_all and ok
        print(f"  {'ok  ' if ok else 'FAIL'} {name}{'' if ok else ' :: ' + detail}")

    with tempfile.TemporaryDirectory() as d:
        ledger = Path(d) / "authority-ledger.jsonl"

        # genesis: a pure authority event (no model) — no receipt binding required
        e0 = emit_ledger_event(
            ledger, event_type="A2A_GRANT", actor=actor,
            payload={"skill": "retrieve"}, policy={"tier": "T1"},
            decision={"allow": True, "reason": "grant issued"}, grant_id="grant_selftest01")
        say(e0["prev_hash"] == GENESIS_PREV and e0["type"] == "A2A_GRANT",
            "genesis authority event emitted, chains to genesis")

        # governed MCP_CALL bound to its InferenceReceipt (native spine emission)
        ir = _synthetic_inference_receipt(0)
        e1 = emit_ledger_event(
            ledger, event_type="MCP_CALL", actor=actor,
            target={"kind": "mcp_tool", "server": "fs.introspect", "tool": "hash"},
            payload={"args": {"path": "/x"}}, policy={"tier": "T1"},
            inference_receipt=ir, event_ir_ref="worm://event-ir/selftest-0",
            decision={"allow": True, "reason": "within grant"})
        say(e1["prev_hash"] == e0["hash"], "MCP_CALL chains to prior entry")
        say(e1["evidence_refs"]["event_ir_hash"] == sha256(canonical(ir)),
            "InferenceReceipt binding is the real content hash (cross-spine)")

        ok, msg = verify_ledger(ledger, validator)
        say(ok, "full chain verifies", msg)

        # AC-1 teeth: an MCP_CALL with NO receipt binding is refused at emit time
        try:
            emit_ledger_event(ledger, event_type="MCP_CALL", actor=actor,
                              payload={"args": {}}, policy={"tier": "T1"})
            say(False, "AC-1: unbound MCP_CALL refused", "emit succeeded")
        except LedgerEmissionError as e:
            say(e.code == "receipt-required", "AC-1: unbound MCP_CALL refused (fail-closed)", e.code)

        # bypass teeth: a hand-crafted MCP_CALL that skipped the emitter (valid chain, no binding)
        bypass = Path(d) / "bypass.jsonl"
        emit_ledger_event(bypass, event_type="A2A_HELLO", actor=actor,
                          payload={"hi": True}, policy={})
        prev = _last_entry(bypass)
        forged = {
            "event_id": "evt_forged00", "ts": "2026-08-03T00:00:01Z", "type": "MCP_CALL",
            "actor": actor, "payload_hash": sha256("{}"), "policy_hash": sha256("{}"),
            "prev_hash": prev["hash"],
        }
        forged["hash"] = _entry_hash(forged["prev_hash"], forged)  # chain-valid but spine-bypassing
        with bypass.open("a", encoding="utf-8") as f:
            f.write(canonical(forged) + "\n")
        okb, msgb = verify_ledger(bypass, validator)
        say(not okb and "spine-bypass" in msgb, "bypass MCP_CALL caught by verifier", msgb)

        # tamper teeth: mutate a sealed field, chain must break
        lines = ledger.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0]); first["payload_hash"] = sha256("mutated")
        lines[0] = canonical(first)
        ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
        okt, msgt = verify_ledger(ledger, validator)
        say(not okt, "tamper breaks the chain", msgt)

    print("SELFTEST:", "OK" if ok_all else "FAILED")
    return 0 if ok_all else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true", help="run emitter/verifier selftest (teeth both ways)")
    g.add_argument("--verify", metavar="LEDGER", help="verify an existing ledger .jsonl chain")
    args = ap.parse_args(argv[1:])

    if args.selftest:
        return _selftest()

    validator = build_validator()
    ok, msg = verify_ledger(Path(args.verify), validator)
    print(("OK: " if ok else "ERR: ") + msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
