# MCP A2A Zero Trust

MCP A2A Zero Trust is the control-zone security kernel for mediated authority across MCP tools, A2A agents, AG-UI interfaces, ANP network peers, Human User Agents, providers, and workspace runtimes.

This repository is not merely a provider marketplace and not merely an MCP server. It owns the zero-trust authority model that decides whether a provider, tool, agent, network peer, interface, or runtime binding may exist, what grants it receives, what attestations are required, what ledger events must be emitted, and which side effects are forbidden or approval-gated.

## Canonical role

Within the SocioProphet estate this repository is the canonical home for:

- Provider capability registry semantics.
- MCP server and tool profile trust boundaries.
- A2A agent profile and delegation boundaries.
- AG-UI human-facing event authority boundaries.
- ANP peer, discovery, route, and message authority boundaries.
- Human User Agent approval and consent mediation.
- Grant request, grant decision, and grant ledger contracts.
- Provider/tool/agent/interface/network attestations.
- Forbidden capability profiles.
- Marketplace admission rules for trusted providers.

## Protocol authority stack

| Surface | Authority question |
|---|---|
| HUA | Which human approval, consent, denial, or delegation event authorizes work? |
| AG-UI | Which user-facing events, state updates, UI intents, and approval requests may be emitted? |
| A2A | Which agent may delegate, coordinate, receive, or escalate work? |
| MCP | Which tools, data sources, providers, and workflows may be called? |
| ANP | Which peers may be discovered, addressed, routed to, messaged, or quarantined? |

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
- Define AG-UI interface profiles and event authority profiles.
- Define ANP network peer profiles and route/discovery grants.
- Define grant requests, grant decisions, and authority-ledger events.
- Define trust tiers and forbidden capabilities.
- Provide examples for GitHub, local workspace, SourceOS device, Human User Agent, and local agent network providers.

No v0 artifact grants arbitrary shell execution, raw secret enumeration, production deployment, repository deletion, branch-protection modification, package publishing, signing authority, autonomous marketplace admission, or unrestricted network egress.

## Documentation map

| Topic | File |
|---|---|
| Home and scope ADR | `docs/adr/ZT-MCP-ADR-0001-home-and-scope.md` |
| Authority model | `docs/architecture/authority-model.md` |
| Protocol stack | `docs/architecture/protocol-stack.md` |
| Forbidden capabilities | `policy/forbidden-capabilities.v0.yaml` |
| Trust tiers | `policy/trust-tiers.v0.yaml` |
| Example providers | `examples/providers/` |
| Example profiles | `examples/ag-ui/`, `examples/anp/`, `examples/mcp/`, `examples/a2a/` |
