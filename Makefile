.PHONY: deps verify verify-carriers verify-ledger verify-policy audit-issues gen-index clean
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

verify-policy: deps
	./scripts/guard_repo_root.sh
	.venv/bin/python ./scripts/verify_policy.py

# T7-17: native hash-chained LedgerEvent emission bound to the model-plane receipt spine.
verify-ledger: deps
	./scripts/guard_repo_root.sh
	.venv/bin/python ./tools/ledger_receipt.py --selftest
	.venv/bin/python ./tools/ledger_receipt.py --verify examples/ledger_chain.example.jsonl
	.venv/bin/python -m pytest tests/test_ledger_receipt.py

verify: deps gen-index verify-carriers verify-ledger verify-policy
	./scripts/guard_repo_root.sh
	.venv/bin/python ./scripts/verify_schemas.py
	.venv/bin/python ./scripts/verify_policy.py

audit-issues:
	./scripts/guard_repo_root.sh
	./scripts/audit_issues.py

clean:
	rm -rf .venv
