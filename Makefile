.PHONY: setup test lint verify demo clean

setup:  ## Install the package (editable) with dev + openai extras
	cd backend && pip install -e ".[dev,openai]"

test:  ## Run the offline test suite
	cd backend && pytest -q

lint:  ## Static checks (install ruff/mypy separately if desired)
	cd backend && python -m compileall -q src

verify: lint test  ## The gate: lint + tests

demo:  ## Ingest the sample corpus and run a couple of questions
	cd backend && GROUNDED_DB=demo.db grounded reset || true
	cd backend && GROUNDED_DB=demo.db grounded ingest sample_corpus
	cd backend && GROUNDED_DB=demo.db grounded ask "do naps help memory" -k 3

clean:  ## Remove build artefacts and demo databases
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.db' -delete
	rm -rf backend/*.egg-info backend/build backend/dist
