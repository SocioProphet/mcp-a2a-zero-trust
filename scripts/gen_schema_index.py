#!/usr/bin/env python3
import json, hashlib, pathlib

def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return "sha256:" + h.hexdigest()

def main():
    root = pathlib.Path(".")
    schema_files = [p for p in sorted(root.glob("schemas/**/*.json")) if p.name != "index.json"]

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
    out_path = root / "schemas/index.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"OK: wrote {out_path} with {len(items)} schema entries")

if __name__ == "__main__":
    main()
