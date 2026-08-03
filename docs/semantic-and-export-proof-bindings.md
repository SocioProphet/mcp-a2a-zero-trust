# Semantic and Export Proof Bindings

This repository carries the runtime governance contracts for grants, policy decisions, and ledger events.

This overlay adds `RuntimeEvidenceRefs` so runtime objects can reference:
- Event-IR inputs from the semantic identity lane,
- semantic proof artifacts from the prime-identity lane,
- HDT decision summaries from the export/readiness lane,
- workload attestation bundles from the workload-identity lane.

## Why

The runtime layer should bind to semantic and export-governance evidence without embedding full artifacts into every grant or ledger entry.
Reference-plus-hash gives portability, replayability, and audit integrity while keeping payloads compact.

## Bound objects

The following objects now accept `evidence_refs`:
- `Grant`
- `PolicyDecision`
- `LedgerEvent`

`LedgerEvent` also gains optional `grant_id` so grant issuance and downstream MCP activity can be stitched together without guessing.

## Reference semantics

A runtime object may include any subset of the following references:
- `event_ir_ref` and `event_ir_hash`
- `semantic_proof_ref` and `semantic_proof_hash`
- `hdt_decision_ref` and `hdt_decision_hash`
- `attestation_bundle_ref` and `attestation_bundle_hash`

These are references, not embedded payloads. Full artifacts remain in their source systems or evidence stores.

## Native emission and the receipt law (T7-17)

Declaring `evidence_refs` is not enough on its own — an optional field can be silently omitted, which
is how an agent-to-agent tool call can be logged while **bypassing the model-plane receipt spine**.
`tools/ledger_receipt.py` makes emission native and enforced:

- `emit_ledger_event()` writes a **hash-chained** `LedgerEvent` — it computes `payload_hash`,
  `policy_hash`, links `prev_hash` to the prior entry's `hash`, and seals each entry with
  `hash = sha256(prev_hash + canonical(event))`. The canonicalization (sorted-key compact JSON +
  sha256) is byte-compatible with the estate receipt emitters (`inference_receipt_emitter.py`,
  `proof-artifact-spine`), so the whole estate shares one append-only, tamper-evident spine
  discipline.
- **The receipt law (AC-1), fail-closed.** For tool/inference dispatch event types
  (`MCP_CALL`, `MCP_RESULT`, `OP_TOOL_INVOKE`) the model-plane **InferenceReceipt** binding is
  mandatory: supply the receipt (its content hash — `sha256(canonical(receipt))`, exactly what the
  model-plane ledger computes — is bound into `event_ir_hash`) or an explicit
  `event_ir_ref` + `event_ir_hash`. No binding ⇒ the event is **not emitted** and nothing is
  governed. The receipt is referenced, never forked.
- `verify_ledger()` independently re-checks the chain (links + hash recompute), schema conformance,
  and the binding law — so a dispatch event hand-crafted around the emitter, or a tampered entry, is
  caught. Teeth both ways are covered by `tests/test_ledger_receipt.py` and the `--selftest`; both run
  under `make verify` (`make verify-ledger`).

Productionising routes these through the shared ledger service behind the `Ledger.Push` triRPC verb
(ADR-0001) so the InferenceReceipt, ProofArtifact, and authority-LedgerEvent streams share one
physical ledger; the mechanics here are contract-first and byte-compatible with that path.
