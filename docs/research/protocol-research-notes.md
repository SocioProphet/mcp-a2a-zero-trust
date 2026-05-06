# Protocol Research Notes: MCP, A2A, AG-UI, and ANP

## Status

Research seed for the zero-trust authority model.

## Purpose

This note records the protocol landscape that `mcp-a2a-zero-trust` must govern. The repository does not redefine these upstream protocols. It defines the zero-trust mediation, grant, attestation, ledger, and capability-registry layer that makes them safe to compose inside the SocioProphet estate.

## AG-UI

AG-UI, the Agent-User Interaction Protocol, is an open, lightweight, event-based protocol for connecting AI agents to user-facing applications. The protocol standardizes how agent state, UI intents, tool progress, user interaction, and frontend/backend agent events flow between an agent runtime and a frontend.

Primary source:

- https://docs.ag-ui.com/introduction
- https://docs.ag-ui.com/agentic-protocols
- https://docs.ag-ui.com/concepts/architecture
- https://github.com/ag-ui-protocol/ag-ui

Important architectural facts:

- AG-UI is agent-to-user, not agent-to-tool and not agent-to-agent.
- AG-UI is event-driven and supports bidirectional interaction.
- AG-UI complements MCP and A2A rather than replacing them.
- AG-UI can front agents that also speak MCP and A2A.
- AG-UI is not itself a generative UI schema, but it can carry or interoperate with generative UI specs.

Zero-trust interpretation:

AG-UI must be treated as a human-facing authority surface. UI events can request approval, steer execution, display claims, expose tool progress, mount generated views, or represent consent. Therefore AG-UI events require provenance, origin binding, grant scope, replay semantics, and prompt-injection boundaries.

## ANP

ANP, the Agent Network Protocol, is an open-source agent communication protocol intended to support secure discovery, identity, negotiation, and collaboration among agents. Its documentation frames ANP as an HTTP-like protocol layer for the agent internet era.

Primary source:

- https://agentnetworkprotocol.com/en/docs/
- https://agentnetworkprotocol.com/en/docs/introduction/
- https://agentnetworkprotocol.com/en/specs/
- https://agentnetworkprotocol.com/en/specs/03-did-wba-method-specification/
- https://agentnetworkprotocol.com/en/specs/07-anp-agent-description-protocol-specification/
- https://github.com/agent-network-protocol/AgentNetworkProtocol

Important architectural facts:

- ANP focuses on agent communication and network-level collaboration.
- ANP includes identity and encryption concepts based on W3C DID patterns.
- ANP includes a meta-protocol layer for protocol negotiation.
- ANP includes an application protocol layer for describing capabilities and supported interfaces.
- ANP specifications use JSON-LD for agent description and discovery surfaces.
- ANP agent descriptions may interoperate with OpenAPI, JSON-RPC, and MCP-style interface descriptions.

Zero-trust interpretation:

ANP must be treated as the network authority surface. Discovery, route grants, peer descriptions, DID identity assertions, protocol negotiation, and capability advertisements are all security-sensitive. ANP metadata must never be treated as trusted merely because it is discoverable. It must be verified, scoped, policy-bound, and ledgered.

## MCP

MCP is the agent-to-tool and agent-to-context surface. In this repository it is governed as a provider/tool authority binding rather than as a generic plugin mechanism.

Zero-trust interpretation:

Every MCP server and tool must declare capability scope, side-effect tier, runtime profile, grant requirements, and output provenance. Generic shell, secret enumeration, arbitrary filesystem, and unrestricted network tools are prohibited in the default profiles.

## A2A

A2A is the agent-to-agent coordination and delegation surface. In this repository it is governed as a delegation and responsibility-transfer boundary.

Zero-trust interpretation:

Every A2A interaction must bind delegated authority, task scope, sender/receiver identities, escalation rules, cancellation rules, and evidence requirements.

## Protocol stack summary

| Layer | Protocol | Governed authority |
|---|---|---|
| Human / user-facing interaction | AG-UI | Consent, approval, event display, state update, human steering |
| Agent-to-agent coordination | A2A | Delegation, collaboration, task routing, escalation |
| Agent-to-tool/context/provider access | MCP | Tool invocation, context access, workflow/data-source authority |
| Agent networking | ANP | Discovery, identity, route, peer messaging, protocol negotiation |

## Design implication

The correct unit of governance is not a plugin, tool, provider, or UI component. The correct unit is a ledgered authority event:

1. A principal asks for authority.
2. A policy evaluates the request.
3. A grant is issued, denied, or approval-gated.
4. The operation executes only within the grant scope.
5. Evidence and ledger events record what happened.
6. Downstream systems consume only the resulting bounded artifacts.
