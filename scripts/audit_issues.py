#!/usr/bin/env python3
import json, re, subprocess, sys

REPO = "SocioProphet/mcp-a2a-zero-trust"

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or ""), (p.stderr or "")

def main() -> int:
    code, out, err = run([
        "gh","issue","list",
        "--repo", REPO,
        "--limit","500",
        "--state","all",
        "--json","number,title,body",
    ])

    out = out.strip()
    err = err.strip()

    # Fail closed: if gh didn't emit JSON, show stderr and stop.
    if code != 0 or not out:
        print("ERR: gh issue list did not return JSON.")
        if err:
            print("---- gh stderr ----")
            print(err)
        return 2

    try:
        issues = json.loads(out)
    except Exception as e:
        print("ERR: could not parse JSON from gh output:", repr(e))
        print("---- gh stdout (first 300 chars) ----")
        print(out[:300])
        if err:
            print("---- gh stderr ----")
            print(err)
        return 2

    missing = []
    for it in issues:
        body = it.get("body") or ""
        has_dod = bool(re.search(r"\b(Definition of Done|DoD)\b", body, re.I))
        has_acc = bool(re.search(r"\b(Acceptance Criteria|Acceptance)\b", body, re.I))
        if not (has_dod and has_acc):
            missing.append((it.get("number"), has_dod, has_acc, it.get("title","")))

    print(f"OK: scanned {len(issues)} issues in {REPO}")
    if missing:
        print("ERR: issues missing required sections (number | DoD | Acceptance | title):")
        for n, d, a, t in missing:
            print(f"- #{n} | DoD={d} | Acceptance={a} | {t}")
        return 2

    print("OK: every issue contains DoD + Acceptance sections")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
