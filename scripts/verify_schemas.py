import json, glob, sys, pathlib
from datetime import datetime, timezone

def load_json(p: str):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))

def main() -> int:
    # 1) JSON parse check for every .json file
    json_files = sorted(glob.glob("**/*.json", recursive=True))
    bad = 0
    for f in json_files:
        try:
            load_json(f)
        except Exception as e:
            print(f"ERR: invalid JSON: {f}: {e}")
            bad += 1
    if bad:
        return 2

    # 2) Required files present
    required = [
        "mcp/registry/capability_registry.schema.json",
        "schemas/canonical/attestation_bundle.schema.json",
        "schemas/canonical/quorum_proof.schema.json",
        "schemas/canonical/policy_decision.schema.json",
        "schemas/canonical/grant.schema.json",
        "ledger/schema.json",
        "schemas/interop/trust_boundary.schema.json",
        "schemas/interop/delegated_authority.schema.json",
        "schemas/interop/operation_command.schema.json",
        "schemas/interop/tool_grant_check.schema.json",
        "schemas/interop/interop_failure.schema.json",
        "schemas/interop/interop_diagnostics.schema.json",
        "schemas/workspace_context/workspace_context_capability_grant_profile.schema.json",
    ]
    for r in required:
        if not pathlib.Path(r).is_file():
            print(f"ERR: missing required file: {r}")
            return 2

    # 3) Validate examples against schemas using a local Registry keyed by $id
    try:
        import jsonschema
        from referencing import Registry, Resource
    except Exception as e:
        print("ERR: missing dependency (install via pip in venv):", e)
        return 2

    # Load all schemas we own and register them by $id
    schema_files = sorted(set(
        glob.glob("schemas/**/*.json", recursive=True)
        + glob.glob("ledger/*.json", recursive=True)
        + glob.glob("mcp/registry/*.json", recursive=True)
    ))

    pairs = []
    for sf in schema_files:
        doc = load_json(sf)
        sid = doc.get("$id")
        if sid:
            pairs.append((sid, Resource.from_contents(doc)))

    registry = Registry().with_resources(pairs)

    schema_map = {
        "examples/attestation_bundle.example.json": "schemas/canonical/attestation_bundle.schema.json",
        "examples/quorum_proof.example.json": "schemas/canonical/quorum_proof.schema.json",
        "examples/policy_decision.example.json": "schemas/canonical/policy_decision.schema.json",
        "examples/grant.example.json": "schemas/canonical/grant.schema.json",
        "examples/ledger_event.example.json": "ledger/schema.json",
        "examples/runtime_evidence_refs.example.json": "schemas/governance/runtime_evidence_refs.schema.json",
        "examples/trust_boundary.example.json": "schemas/interop/trust_boundary.schema.json",
        "examples/delegated_authority.example.json": "schemas/interop/delegated_authority.schema.json",
        "examples/operation_command.example.json": "schemas/interop/operation_command.schema.json",
        "examples/tool_grant_check.example.json": "schemas/interop/tool_grant_check.schema.json",
        "examples/interop_failure.example.json": "schemas/interop/interop_failure.schema.json",
        "examples/interop_diagnostics.example.json": "schemas/interop/interop_diagnostics.schema.json",
        "examples/workspace_context_capability_grant_profile.example.json": "schemas/workspace_context/workspace_context_capability_grant_profile.schema.json",
        "examples/agent_class_grant.example.json": "schemas/governance/agent_class_grant.schema.json",
    }

    for ex_path, schema_path in schema_map.items():
        ex = load_json(ex_path)
        schema = load_json(schema_path)

        validator = jsonschema.Draft202012Validator(schema, registry=registry)
        errors = sorted(validator.iter_errors(ex), key=lambda e: (list(e.path), e.message))
        if errors:
            e = errors[0]
            where = "$" + "".join([f"[{repr(p)}]" if isinstance(p, int) else f".{p}" for p in e.path])
            print(f"ERR: example fails schema: {ex_path} vs {schema_path}")
            print(f"  at: {where}")
            print(f"  msg: {e.message}")
            return 2

    print("OK: all JSON parsed, required schemas present, examples validated @", datetime.now(timezone.utc).isoformat().replace("+00:00","Z"))
    return 0

if __name__ == "__main__":
    sys.exit(main())