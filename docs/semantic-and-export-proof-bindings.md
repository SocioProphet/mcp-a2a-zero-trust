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
