# ---- Configuration ----
MAIN   := a_maze_ing.py
CONFIG := config.txt
VENV   := .venv

# Use the virtualenv if it exists, otherwise fall back to system python
PY := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)

FLAKE_FLAGS := --exclude $(VENV),.git,__pycache__,.mypy_cache,build
MYPY_EXCL   := --exclude '^($(VENV)|build)/'

MYPY_FLAGS := --warn-return-any --warn-unused-ignores --ignore-missing-imports \
              --disallow-untyped-defs --check-untyped-defs

.PHONY: install run debug clean lint lint-strict

install:
	python3 -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install flake8 mypy

run:
	$(PY) $(MAIN) $(CONFIG)

debug:
	$(PY) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	rm -rf build *.egg-info

lint:
	$(PY) -m flake8 $(FLAKE_FLAGS) .
	$(PY) -m mypy . $(MYPY_EXCL) $(MYPY_FLAGS)

lint-strict:
	$(PY) -m flake8 $(FLAKE_FLAGS) .
	$(PY) -m mypy . $(MYPY_EXCL) --strict