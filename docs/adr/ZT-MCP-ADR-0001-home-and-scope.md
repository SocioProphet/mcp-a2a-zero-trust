# ZT-MCP-ADR-0001: Home and Scope for MCP/A2A/AG-UI/ANP Zero Trust

## Status

Accepted.

## Decision

`SocioProphet/mcp-a2a-zero-trust` is the canonical home for the zero-trust authority model governing MCP, A2A, AG-UI, ANP, Human User Agent mediation, provider capability registries, grants, attestations, ledgers, and marketplace admission rules.

This repository is the trust kernel for mediated authority. It is not merely a product marketplace, not merely an MCP server, not merely an agent runtime, and not merely a UI integration layer.

## Context

The SocioProphet estate already declares this repository as a security/control-zone component with required capabilities for policy, attestation, grants, ledgering, and capability registry behavior. That placement makes this repository the appropriate authority boundary for provider and protocol mediation.

The relevant protocol layers are:

- AG-UI: Agent to user-facing interface event stream.
- MCP: Agent to tool, workflow, and data-source access.
- A2A: Agent to agent coordination and delegation.
- ANP: Agent network discovery, addressing, communication, and network-level collaboration.

The provider marketplace sits across those layers, but the marketplace itself is subordinate to zero-trust authorization. A provider listing is not trusted merely because it exists; it must have declared capabilities, trust tier, policy grants, attestations, side-effect classification, and ledgered usage.

## Architecture rule

The repository owns the question:

> May this human, agent, provider, tool, network peer, or runtime binding exist and act under these constraints?

Neighboring repositories answer downstream questions:

- `SocioProphet/agentplane`: how approved work is placed, run, evidenced, and replayed.
- `SocioProphet/sociosphere`: how the estate materializes, validates, and governs this repository and its consumers.
- `SocioProphet/prophet-platform`: how approved providers and marketplace capabilities are presented to users and workspaces.
- `SocioProphet/policy-fabric`: how generalized policy semantics are expressed and reused.
- `SocioProphet/socioprophet-standards-storage`: how durable manifests, reports, ledgers, and provenance schemas are stored.

## Consequences

This repository must define schemas and policy artifacts for:

- Provider manifests.
- Provider capabilities.
- Provider trust tiers.
- MCP server profiles.
- MCP tool manifests.
- A2A agent profiles.
- A2A capability bindings.
- AG-UI interface profiles.
- AG-UI event authority boundaries.
- ANP network peer profiles.
- ANP route and discovery grants.
- Human User Agent approval and consent boundaries.
- Grant requests, grant decisions, and authority-ledger events.
- Forbidden capabilities and side-effect tiers.

## Non-goals

The initial scope does not implement arbitrary command execution, package publishing, signing, production deployment, raw secret enumeration, repository deletion, branch-protection modification, unrestricted network egress, or autonomous marketplace admission.
