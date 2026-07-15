PYTHON := python3
PIP := pip

# Map used by `make run` / `make debug`. Override on the CLI, e.g.
#   make run MAP=maps/easy_2.map
MAP ?= maps/example.map

.PHONY: install run debug clean lint lint-strict test

install:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py $(MAP)

debug:
	$(PYTHON) -m pdb main.py $(MAP)

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

test:
	pytest -q
