VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
STAMP := $(VENV)/.deps.stamp

.PHONY: deps verify clean

$(STAMP):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip >/dev/null
	$(PIP) install jsonschema check-jsonschema >/dev/null
	touch $(STAMP)

deps: $(STAMP)

verify: deps
	./scripts/guard_repo_root.sh
	$(PY) ./scripts/verify_schemas.py

clean:
	rm -rf $(VENV)
