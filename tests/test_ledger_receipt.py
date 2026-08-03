#!/usr/bin/env python3
"""T7-17 conformance — native, spine-bound LedgerEvent emission.

Teeth both ways:
  * a governed action emits a valid, schema-conformant, hash-chained LedgerEvent, and a
    tool/inference dispatch binds the model-plane InferenceReceipt by its real content hash;
  * a bypassed action is caught — an inference/tool dispatch with no InferenceReceipt binding is
    refused at emit time (AC-1, fail-closed) and, if hand-crafted around the emitter, rejected by
    the verifier;
  * tampering with any sealed field breaks the chain;
  * pure authority events (grants/hellos) need no receipt binding;
  * the committed example chain verifies.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import ledger_receipt as lr  # noqa: E402

ACTOR = {"spiffe_id": "spiffe://sourceos/inception"}


def _receipt(seq: int = 0) -> dict:
    return {
        "id": f"urn:srcos:inference-receipt:test-{seq}", "type": "InferenceReceipt",
        "specVersion": "2.1.0", "issuedAt": "2026-08-03T00:00:00Z", "providerDaemon": "inferenced",
        "tier": "T1", "baseModelDigest": "sha256:" + "a" * 64, "task": "test",
        "inputHash": lr.sha256(f"in {seq}"), "outputHash": lr.sha256(f"out {seq}"),
        "dataResidencyClass": "on_device_only", "ledgerSeq": seq,
    }


def _emit_mcp(ledger, **over):
    kw = dict(event_type="MCP_CALL", actor=ACTOR,
              target={"kind": "mcp_tool", "server": "graph.query", "tool": "cypher"},
              payload={"args": {"lemma": "baxter"}}, policy={"tier": "T1"},
              inference_receipt=_receipt(), event_ir_ref="worm://event-ir/test-0")
    kw.update(over)
    return lr.emit_ledger_event(ledger, **kw)


def _validator():
    return lr.build_validator()


def test_governed_dispatch_emits_conformant_chained_receipt(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    e0 = lr.emit_ledger_event(ledger, event_type="A2A_GRANT", actor=ACTOR,
                              payload={"skill": "retrieve"}, policy={"tier": "T1"},
                              decision={"allow": True, "reason": "grant"}, grant_id="grant_test0001")
    assert e0["prev_hash"] == lr.GENESIS_PREV
    e1 = _emit_mcp(ledger)
    assert e1["prev_hash"] == e0["hash"]                      # native chaining
    assert e1["payload_hash"].startswith("sha256:")
    # the binding is the REAL content hash of the InferenceReceipt (cross-spine, not a placeholder)
    assert e1["evidence_refs"]["event_ir_hash"] == lr.sha256(lr.canonical(_receipt()))
    ok, msg = lr.verify_ledger(ledger, _validator())
    assert ok, msg


def test_emitted_events_validate_against_ledger_schema(tmp_path):
    v = _validator()
    assert v is not None, "jsonschema/referencing must be installed for schema conformance"
    ledger = tmp_path / "ledger.jsonl"
    _emit_mcp(ledger, event_type="A2A_HELLO", inference_receipt=None, event_ir_ref=None,
              target=None, payload={"hi": True}, policy={})
    _emit_mcp(ledger)
    for line in ledger.read_text().splitlines():
        entry = json.loads(line)
        assert list(v.iter_errors(entry)) == []


def test_ac1_unbound_dispatch_refused_fail_closed(tmp_path):
    """An inference/tool dispatch with no InferenceReceipt binding is not a governed action."""
    ledger = tmp_path / "ledger.jsonl"
    with pytest.raises(lr.LedgerEmissionError) as ei:
        lr.emit_ledger_event(ledger, event_type="MCP_CALL", actor=ACTOR,
                             payload={"args": {}}, policy={"tier": "T1"})
    assert ei.value.code == "receipt-required"
    assert not ledger.exists()  # nothing written when the receipt cannot be bound


def test_receipt_hash_mismatch_refused(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    with pytest.raises(lr.LedgerEmissionError) as ei:
        _emit_mcp(ledger, event_ir_hash="sha256:" + "9" * 64)  # wrong hash for this receipt
    assert ei.value.code == "receipt-hash-mismatch"


def test_bypass_event_caught_by_verifier(tmp_path):
    """A hand-crafted dispatch that skipped the emitter: chain-valid but spine-bypassing."""
    ledger = tmp_path / "ledger.jsonl"
    lr.emit_ledger_event(ledger, event_type="A2A_HELLO", actor=ACTOR, payload={"hi": True}, policy={})
    prev = json.loads(ledger.read_text().splitlines()[-1])
    forged = {"event_id": "evt_forged001", "ts": "2026-08-03T00:00:02Z", "type": "MCP_CALL",
              "actor": ACTOR, "payload_hash": lr.sha256("{}"), "policy_hash": lr.sha256("{}"),
              "prev_hash": prev["hash"]}
    forged["hash"] = lr._entry_hash(forged["prev_hash"], forged)  # chain is intact...
    with ledger.open("a", encoding="utf-8") as f:
        f.write(lr.canonical(forged) + "\n")
    ok, msg = lr.verify_ledger(ledger, _validator())
    assert not ok and "spine-bypass" in msg, msg          # ...but the binding law catches it


def test_tamper_breaks_chain(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    lr.emit_ledger_event(ledger, event_type="A2A_GRANT", actor=ACTOR,
                         payload={"a": 1}, policy={"tier": "T1"})
    _emit_mcp(ledger)
    lines = ledger.read_text().splitlines()
    first = json.loads(lines[0]); first["payload_hash"] = lr.sha256("mutated")
    lines[0] = lr.canonical(first)
    ledger.write_text("\n".join(lines) + "\n")
    ok, msg = lr.verify_ledger(ledger, _validator())
    assert not ok, "tampered sealed field must break verification"


def test_pure_authority_event_needs_no_binding(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    e = lr.emit_ledger_event(ledger, event_type="A2A_GRANT", actor=ACTOR,
                             payload={"skill": "x"}, policy={"tier": "T1"})
    assert "evidence_refs" not in e
    ok, _ = lr.verify_ledger(ledger, _validator())
    assert ok


def test_committed_example_chain_verifies():
    example = ROOT / "examples" / "ledger_chain.example.jsonl"
    assert example.is_file(), "committed example chain must exist"
    ok, msg = lr.verify_ledger(example, _validator())
    assert ok, msg
