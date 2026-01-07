#!/usr/bin/env python3
import json, hashlib, pathlib

def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return "sha256:" + h.hexdigest()

def discover_schema_files(root: pathlib.Path):
    files = []
    # canonical + any future schemas we keep under schemas/
    for p in sorted(root.glob("schemas/**/*.json")):
        if p.name == "index.json":
            continue
        files.append(p)

    # MCP registries or other tool contracts
    for p in sorted(root.glob("mcp/**/*.schema.json")):
        files.append(p)

    # ledger contract (not named *.schema.json)
    lp = root / "ledger" / "schema.json"
    if lp.is_file():
        files.append(lp)

    # de-dupe while preserving order
    seen = set()
    out = []
    for p in files:
        s = str(p.as_posix())
        if s in seen:
            continue
        seen.add(s)
        out.append(p)
    return out

def main():
    root = pathlib.Path(".")
    schema_files = discover_schema_files(root)

    items = []
    for p in schema_files:
        data = json.loads(p.read_text(encoding="utf-8"))
        items.append({
            "path": str(p.as_posix()),
            "$id": data.get("$id",""),
            "title": data.get("title",""),
            "sha256": sha256_file(p),
        })

    out = {"version": 1, "count": len(items), "items": items}
    out_path = root / "schemas" / "index.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"OK: wrote {out_path} with {len(items)} schema entries")

if __name__ == "__main__":
    main()
