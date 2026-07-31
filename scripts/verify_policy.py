#!/usr/bin/env python3
"""Verify the agent-class policy layer (trust tiers + forbidden capabilities).

These policies are the zero-trust enforcement surface for the AgentPassport
five-class model. The invariants that make them safe are asserted here so a
malformed or under-specified policy fails CI rather than shipping:

  * all five agent classes are mapped to a tier in 1..4;
  * third_party's forbidden list covers the non-negotiable bans
    (suppress_user_authorization_prompt, system_bundle, persistent_system_banner);
  * every forbidden-capability rule names a seam (SEAM-###) and a non-empty
    forbidden_for; the SEAM-013 telemetry rule is gate_type: advisory;
  * the two files are internally consistent (a class banned from suppression in
    trust-tiers is also banned in forbidden-capabilities).
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml is in requirements-dev.txt
    print("FAIL: pyyaml not installed; add pyyaml to requirements-dev.txt")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
TIERS = ROOT / "policy" / "trust-tiers.v1.yaml"
FORBIDDEN = ROOT / "policy" / "forbidden-capabilities.v1.yaml"

CLASSES = {"system_core", "intelligence_automation", "app_helper", "legacy_bridge", "third_party"}
THIRD_PARTY_BANS = {"suppress_user_authorization_prompt", "system_bundle", "persistent_system_banner"}
SEAM_RE = __import__("re").compile(r"^SEAM-[0-9]{3}$")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(2)


def load(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing policy file: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def verify_tiers() -> dict:
    doc = load(TIERS)
    mapping = doc.get("agent_class_tier_mapping") or {}
    if set(mapping) != CLASSES:
        fail(f"trust-tiers must map exactly the five classes, got {sorted(mapping)}")
    for cls, spec in mapping.items():
        tier = spec.get("tier")
        if tier not in (1, 2, 3, 4):
            fail(f"{cls}: tier must be 1..4, got {tier!r}")
    tp = mapping["third_party"].get("forbidden") or []
    missing = THIRD_PARTY_BANS - set(tp)
    if missing:
        fail(f"third_party.forbidden missing required bans: {sorted(missing)}")
    if mapping["system_core"].get("requires_attestation") is not True:
        fail("system_core must set requires_attestation: true")
    return mapping


def verify_forbidden() -> list:
    doc = load(FORBIDDEN)
    rules = doc.get("forbidden_capabilities") or []
    if not rules:
        fail("forbidden_capabilities must be a non-empty list")
    saw_advisory_telemetry = False
    for r in rules:
        cap = r.get("capability")
        if not cap:
            fail(f"rule missing capability: {r}")
        ff = r.get("forbidden_for") or []
        if not ff:
            fail(f"{cap}: forbidden_for must be non-empty")
        for c in ff:
            if c != "all" and c not in CLASSES:
                fail(f"{cap}: forbidden_for has unknown class {c!r}")
        seam = r.get("seam", "")
        if not SEAM_RE.match(str(seam)):
            fail(f"{cap}: seam must be SEAM-### , got {seam!r}")
        if r.get("seam") == "SEAM-013":
            if r.get("gate_type") != "advisory":
                fail("SEAM-013 telemetry rule must be gate_type: advisory")
            saw_advisory_telemetry = True
    if not saw_advisory_telemetry:
        fail("expected a SEAM-013 telemetry rule marked gate_type: advisory")
    return rules


def verify_consistency(mapping: dict, rules: list) -> None:
    # A class banned from suppression in forbidden-capabilities must not be
    # tier-mapped as allowed to suppress. Cross-check third_party specifically.
    suppress_rule = next(
        (r for r in rules if r.get("capability") == "suppress_user_authorization_prompt"),
        None,
    )
    if suppress_rule is None:
        fail("no suppress_user_authorization_prompt forbidden rule")
    banned = set(suppress_rule.get("forbidden_for") or [])
    if "third_party" not in banned:
        fail("third_party must be in the suppress_user_authorization_prompt ban")
    if "suppress_user_authorization_prompt" not in (mapping["third_party"].get("forbidden") or []):
        fail("trust-tiers and forbidden-capabilities disagree on third_party suppression")


def main() -> int:
    mapping = verify_tiers()
    rules = verify_forbidden()
    verify_consistency(mapping, rules)
    print(
        f"OK: trust-tiers (5 classes -> tiers 1..4) and "
        f"forbidden-capabilities ({len(rules)} rules, SEAM-tagged) verified and consistent"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
