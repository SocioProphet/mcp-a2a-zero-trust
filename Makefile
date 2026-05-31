.PHONY: deps verify verify-carriers audit-issues gen-index clean
# venv-based deps (avoids PEP 668 external management issues on macOS)
deps: .venv/.deps.stamp
.venv/.deps.stamp:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip >/dev/null
	.venv/bin/pip install -r requirements-dev.txt >/dev/null
	touch .venv/.deps.stamp

gen-index: deps
	./scripts/guard_repo_root.sh
	.venv/bin/python ./scripts/gen_schema_index.py

verify-carriers: deps
	./scripts/guard_repo_root.sh
	.venv/bin/python -m pytest tests/test_verify_carrier_pps.py

verify: deps gen-index verify-carriers
	./scripts/guard_repo_root.sh
	.venv/bin/python ./scripts/verify_schemas.py

audit-issues:
	./scripts/guard_repo_root.sh
	./scripts/audit_issues.py

clean:
	rm -rf .venv
