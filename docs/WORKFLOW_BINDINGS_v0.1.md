# Workflow bindings v0.1

This change prepares `mcp-a2a-zero-trust` to serve as the canonical trust plane for the
workflow kernel defined in `sociosphere/protocol/agentic-workbench/v1`.

## Canonical objects owned here

- `AttestationBundle`
- `PolicyDecision`
- `Grant`
- `QuorumProof`
- `LedgerEvent`
- `MCP Capability Registry`

## Objects owned elsewhere

The following remain owned by `sociosphere` and MUST reference the canonical trust objects
in this repository by ref/hash rather than duplicating them:

- `WorkflowSpec`
- `WorkflowRun`
- `StepSpec`
- `ArtifactRef`
- `ExecutionEnvelope`
- `ExecutionRecord`
- `ApprovalRequest`
- `TrustProfile`
- workspace policy packs

## Capability generalization

The earlier trust model was MCP-tool-centric (`server/tool/effect`). The workflow kernel
requires capability addressing for multiple execution surfaces:

- `mcp_tool`
- `a2a_skill`
- `deployment`
- `runner_action`

Accordingly, grants, ledger targets, and capability registry entries now expose:

- `kind`
- `capability_ref`
- `capability_digest`
- transport-specific selectors (optional)
- `effect`

## Mandatory trust chain

For any side-effecting step, the canonical chain is:

`AttestationBundle -> PolicyDecision -> QuorumProof (if required) -> Grant -> Dispatch -> LedgerEvent`

## Workflow-native ledger events

This update adds workflow phase events to the ledger enum:

- `WF_VALIDATE`
- `WF_PLACE`
- `WF_DISPATCH`
- `WF_RESULT`
- `WF_REPLAY`
- `WF_COMPENSATE`
- `WF_APPROVAL_REQUEST`
- `WF_APPROVAL_DECISION`

These events complement the existing `A2A_*` and `MCP_*` transport events.

## Examples

See:

- `examples/mcp_step_authorization.example.json`
- `examples/a2a_step_authorization.example.json`
- `examples/deployment_step_authorization.example.json`
