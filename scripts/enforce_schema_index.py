#!/usr/bin/env python3
import json, hashlib, sys
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return "sha256:" + h.hexdigest()

def discover_schema_paths(root: Path):
    files = []

    # canonical + any future schemas under schemas/
    for p in sorted(root.glob("schemas/**/*.json")):
        if p.name == "index.json":
            continue
        files.append(p)

    # MCP/tool contracts (explicitly schema json)
    for p in sorted(root.glob("mcp/**/*.schema.json")):
        files.append(p)

    # ledger contract (not named *.schema.json)
    lp = root / "ledger" / "schema.json"
    if lp.is_file():
        files.append(lp)

    # de-dupe, preserve order
    seen = set()
    out = []
    for p in files:
        sp = p.as_posix()
        if sp in seen:
            continue
        seen.add(sp)
        out.append(p)
    return out

def main():
    root = Path(".")
    idx_path = root / "schemas" / "index.json"
    if not idx_path.is_file():
        print("ERR: missing schemas/index.json (run: python3 scripts/gen_schema_index.py)")
        return 2

    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    if not isinstance(idx, dict) or "items" not in idx or not isinstance(idx["items"], list):
        print("ERR: schemas/index.json malformed (expected {items:[...]})")
        return 2

    expected = discover_schema_paths(root)
    expected_paths = [p.as_posix() for p in expected]
    expected_set = set(expected_paths)

    idx_paths = [it.get("path", "") for it in idx["items"]]
    idx_set = set(idx_paths)

    missing = sorted(expected_set - idx_set)
    extra = sorted(idx_set - expected_set)

    if missing:
        print("ERR: schemas/index.json missing schema files:")
        for p in missing:
            print("  -", p)
        print("Run: python3 scripts/gen_schema_index.py")
        return 2

    if extra:
        print("ERR: schemas/index.json references non-schema files:")
        for p in extra:
            print("  -", p)
        return 2

    seen_ids = set()
    for it in idx["items"]:
        path = it.get("path", "")
        sid = it.get("$id", "")
        want = it.get("sha256", "")
        pp = root / path

        if not pp.is_file():
            print(f"ERR: schema index references missing file: {path}")
            return 2

        got = sha256_file(pp)
        if want != got:
            print(f"ERR: schema index sha256 mismatch for {path}: want {want} got {got}")
            print("Run: python3 scripts/gen_schema_index.py")
            return 2

        if not sid:
            print(f"ERR: schema missing $id (required): {path}")
            return 2

        if sid in seen_ids:
            print(f"ERR: duplicate $id across schemas: {sid}")
            return 2
        seen_ids.add(sid)

    print(f"OK: schemas/index.json enforced (files={len(expected_paths)}, unique_ids={len(seen_ids)})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
