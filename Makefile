.PHONY: deps verify

.venv/.deps.stamp:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip >/dev/null
	.venv/bin/pip install jsonschema check-jsonschema >/dev/null
	touch .venv/.deps.stamp

deps: .venv/.deps.stamp

verify: deps
	./scripts/guard_repo_root.sh
	.venv/bin/python scripts/gen_schema_index.py
	.venv/bin/python scripts/enforce_schema_index.py
	.venv/bin/python ./scripts/verify_schemas.py
\n\n.PHONY: audit-issues\naudit-issues:\n\t./scripts/guard_repo_root.sh\n\t./scripts/audit_issues.py\n