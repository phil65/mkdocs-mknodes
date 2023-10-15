.PHONY: help clean lint test docs serve release bump
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r"^([a-zA-Z_-]+):.*?## (.*)$$", line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: ## remove all build, test, coverage and Python artifacts
	git clean -dfX

test: ## run tests
	hatch run test

mypy: ## run mypy type checking
	hatch run lint-check

docs: ## builds the documentation
	hatch run mkdocs build -v

serve: ## run html server watching file changes in realtime
	hatch run mkdocs serve -v

update: ## update all packages
	hatch run python -m pip --disable-pip-version-check list --outdated --format=json | python -c "import json, sys; print('\n'.join([x['name'] for x in json.load(sys.stdin)]))" | xargs -n1 hatch run python -m pip install -U
