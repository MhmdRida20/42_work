PYTHON := python3

# Map used by `make run` / `make visual` / `make debug`. Override on
# the CLI, e.g.
#   make run MAP=maps/easy/01_linear_path.txt
MAP ?= maps/example.map

.PHONY: install run visual debug clean lint lint-strict test

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) main.py $(MAP)

visual:
	$(PYTHON) main.py $(MAP) --visual

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
	$(PYTHON) -m pytest -q
