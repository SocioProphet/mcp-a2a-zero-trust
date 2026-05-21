# ZT-MCP-ADR-0002: Operation Plane Trust Boundaries for MCP/A2A Interop

## Status

Accepted.

## Decision

All MCP tool invocations and agent-to-agent (A2A) messages that cross a workspace boundary MUST be represented as `OperationCommand` records, scoped to a `TrustBoundary`, and authorized by a `DelegatedAuthority` envelope that references a valid, unexpired `Grant`. Every operation emits a `LedgerEvent` regardless of outcome.

## Context

Issue #17 requires that cross-agent and cross-tool calls cannot bypass policy, ledger, or agent registry authority. The following design concerns motivated this ADR:

1. MCP tool calls and A2A messages are not first-class authority objects in the existing schema set. They are transport events with ledger markers (`MCP_CALL`, `A2A_HELLO`, etc.) but lack explicit trust boundary scoping and delegated authority envelopes.
2. The grant schema captures who may do what, but not the specific cross-boundary call that is being authorized in a given moment.
3. Failure modes (tool unavailable, grant denied, revoked credential, external admin required, policy blocked) are not canonically typed, making programmatic remediation difficult.
4. Diagnostic exports for interop traces have no standard schema, meaning redaction cannot be enforced by contract.

## New schemas

All schemas live under `schemas/interop/` and use `$id` values under `https://sourceos.local/schemas/interop/`.

### TrustBoundary (`trust_boundary.schema.json`)

Declares the policy-governed security boundary around an MCP server, MCP tool, remote agent, connector, or model endpoint. A TrustBoundary record carries:

- `boundary_id`, `kind`, `spiffe_id` — stable identity
- `capability_refs` — capabilities exposed through this boundary
- `policy_hash`, `trust_tier`, `status` — governance state
- `attestation_required`, `grant_required`, `ledger_mode` — enforcement knobs
- `evidence_refs` — links to attestation and event-IR evidence

Suspended and revoked boundaries fail closed for all operations.

### DelegatedAuthority (`delegated_authority.schema.json`)

Authority envelope that accompanies every cross-agent or cross-tool action. Captures:

- `actor` (delegating principal) and `delegate` (receiving agent)
- `operation` — one of the six canonical operation types
- `scope` — capability refs in scope
- `trust_boundary_id` and `grant_id` — explicit references to the scoping boundary and authorizing grant
- `expires_at` — expired envelopes fail closed regardless of grant state
- `constraints` — operational constraints narrowed from or equal to the grant's constraints
- `sig` — signature from the issuing authority

A `DelegatedAuthority` is not itself a grant. It is an ephemeral, scoped claim that references a long-lived `Grant`.

### OperationCommand (`operation_command.schema.json`)

Transport binding for a single interop operation. One `OperationCommand` maps to exactly one `operation` and one `ledger_event_type`. The command cannot be dispatched without referencing a valid, unexpired `DelegatedAuthority`.

| `operation`                          | `transport` | `ledger_event_type` |
|--------------------------------------|-------------|---------------------|
| `mcp.tool.invoke`                    | `mcp`       | `OP_TOOL_INVOKE`    |
| `a2a.message.send`                   | `a2a`       | `OP_MSG_SEND`       |
| `a2a.task.delegate`                  | `a2a`       | `OP_TASK_DELEGATE`  |
| `tool_grant.validate`                | `internal`  | `OP_GRANT_VALIDATE` |
| `tool_grant.revoke`                  | `internal`  | `OP_GRANT_REVOKE`   |
| `interop.diagnostics.export_redacted`| `internal`  | `OP_DIAG_EXPORT`    |

### ToolGrantCheck (`tool_grant_check.schema.json`)

Records the result of a `tool_grant.validate` or `tool_grant.revoke` operation. The `result.valid` field is authoritative: a `false` value MUST cause the calling `OperationCommand` to be rejected. Revoked and expired grants fail closed.

### InteropFailure (`interop_failure.schema.json`)

Canonical failure record for any interop operation that could not be completed. The five failure classes are:

| `failure_class`            | Meaning                                                                  |
|----------------------------|--------------------------------------------------------------------------|
| `tool_unavailable`         | MCP tool or remote agent is not reachable or registered                  |
| `grant_denied`             | No valid grant exists for the requested operation and scope              |
| `credential_revoked`       | Actor's credential or grant has been explicitly revoked                  |
| `external_admin_required`  | Operation requires out-of-band human or admin approval                   |
| `policy_blocked`           | Policy fabric evaluated and explicitly denied this operation             |

All five classes fail closed. Callers MUST NOT retry without external remediation.

### InteropDiagnostics (`interop_diagnostics.schema.json`)

Redacted diagnostic export for interop traces. Before export:

- `credentials`, `prompts`, `payloads`, `identifiers`, `tool_arguments`, `agent_messages`, and `model_outputs` are redacted according to `redaction_policy_hash`.
- `actor_ref` in each `TraceEvent` is an opaque reference, never a raw SPIFFE ID or credential.
- The export itself is an `OP_DIAG_EXPORT` ledger event.

## Updated LedgerEvent schema

Six new event types are added to the `type` enum in `ledger/schema.json`:

- `OP_TOOL_INVOKE` — `mcp.tool.invoke` via the operation plane
- `OP_MSG_SEND` — `a2a.message.send`
- `OP_TASK_DELEGATE` — `a2a.task.delegate`
- `OP_GRANT_VALIDATE` — `tool_grant.validate`
- `OP_GRANT_REVOKE` — `tool_grant.revoke`
- `OP_DIAG_EXPORT` — `interop.diagnostics.export_redacted`

Two optional correlation fields are added:

- `trust_boundary_id` — references the TrustBoundary at which this event was evaluated
- `authority_envelope_id` — references the DelegatedAuthority envelope that scoped this operation

## Mandatory trust chain (updated)

For any interop operation, the canonical chain is:

```
AttestationBundle
  → PolicyDecision
  → QuorumProof (if required)
  → Grant
  → TrustBoundary (scoping)
  → DelegatedAuthority (per-call envelope)
  → OperationCommand (transport binding)
  → LedgerEvent (audit, regardless of outcome)
```

Failures at any step in the chain produce an `InteropFailure` record and a `LedgerEvent` with `decision.allow = false`.

## Dependency rule

The interop layer MUST depend on `agent-registry`, `policy-fabric`, and operation contracts rather than duplicating them. Specifically:

- `TrustBoundary.policy_hash` references a policy owned by `policy-fabric`.
- `DelegatedAuthority.grant_id` references a `Grant` from this repository's canonical schema.
- `OperationCommand.authority_envelope_id` references a `DelegatedAuthority` owned by this repository.
- Agent profiles and skill registrations are owned by `agent-registry`; this repository references them by ID only.

## Hard rule

> Interop is not authority. MCP/A2A calls must be scoped, policy-checked, auditable, and revocable.

A `DelegatedAuthority` envelope without a valid backing `Grant` at a known `TrustBoundary` is rejected. The absence of a `LedgerEvent` is treated as a failure, not a success.

## Consequences

- All MCP and A2A call paths in downstream systems MUST produce `OperationCommand` records before dispatch.
- Grant lifecycle systems MUST emit `OP_GRANT_VALIDATE` and `OP_GRANT_REVOKE` ledger events.
- Diagnostic tooling MUST use `InteropDiagnostics` for any interop trace export and apply the declared redaction policy.
- The `schemas/interop/` directory is the canonical location for all new interop contract schemas.
