# MCP A2A Zero Trust

MCP A2A Zero Trust is the control-zone security kernel for mediated authority across MCP tools, A2A agents, Human User Agents, providers, and workspace runtimes.

This repository is not merely a provider marketplace and not merely an MCP server. It owns the zero-trust authority model that decides whether a provider, tool, agent, or runtime binding may exist, what grants it receives, what attestations are required, what ledger events must be emitted, and which side effects are forbidden or approval-gated.

## Canonical role

Within the SocioProphet estate this repository is the canonical home for:

- Provider capability registry semantics.
- MCP server and tool profile trust boundaries.
- A2A agent profile and delegation boundaries.
- Human User Agent approval and consent mediation.
- Grant request, grant decision, and grant ledger contracts.
- Provider/tool attestations.
- Forbidden capability profiles.
- Marketplace admission rules for trusted providers.

## Boundary with neighboring repositories

- `SocioProphet/sociosphere` declares this repository in the workspace manifest and validates its conformance across the estate.
- `SocioProphet/agentplane` consumes approved decisions and executes validated bundles while emitting evidence and replay artifacts.
- `SocioProphet/prophet-platform` presents approved marketplace and provider surfaces to users and workspaces.
- `SocioProphet/policy-fabric` supplies generalized policy semantics that this repository may bind into grant decisions.
- `SocioProphet/socioprophet-standards-storage` supplies durable storage, manifest, report, and provenance schemas.

## v0 scope

The v0 scope is intentionally conservative:

- Define provider manifests and provider capabilities.
- Define MCP server profiles and MCP tool manifests.
- Define A2A agent profiles and capability bindings.
- Define grant requests, grant decisions, and authority-ledger events.
- Define trust tiers and forbidden capabilities.
- Provide examples for GitHub, local workspace, and SourceOS device providers.

No v0 artifact grants arbitrary shell execution, raw secret enumeration, production deployment, repository deletion, branch-protection modification, package publishing, signing authority, or unrestricted network egress.
