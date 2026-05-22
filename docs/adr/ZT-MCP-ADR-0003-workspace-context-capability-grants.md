# ZT-MCP-ADR-0003: Workspace Context Capability Grants

## Status

Proposed.

## Decision

Workspace Context Fabric operations that cross an agent, tool, provider, or workspace boundary must be represented as explicit capability grants in MCP/A2A Zero Trust.

This repository owns the mediated-authority profile for those grants. It does not own Workroom, ContextGraph, platform record, execution evidence, recall promotion, or agent authority-state semantics.

## Capability family

The initial family is:

- `workspace.context.capture`
- `workspace.context.project`
- `workspace.context.share`
- `workspace.context.recall.propose`
- `workspace.context.recall.promote`
- `workspace.context.continuation.record`

## Required refs

A Workspace Context capability grant profile should preserve refs to:

- Workroom or ProfessionalWorkroom;
- ContextGraph;
- WorkspaceContextRuntimeBinding;
- Agent Registry authority binding;
- AgentPlane evidence;
- Prophet Platform record;
- Memory Mesh recall promotion packet;
- policy decisions;
- evidence records.

## Boundary rule

A capability grant permits a bounded operation. It does not itself store workspace context, perform a provider call, approve durable recall, or override policy.

## Contract

The first contract is:

```text
schemas/workspace_context/workspace_context_capability_grant_profile.schema.json
examples/workspace_context_capability_grant_profile.example.json
```

The existing `make verify` path validates the example against the schema.
