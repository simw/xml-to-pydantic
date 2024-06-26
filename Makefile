.DEFAULT_TARGET: help
sources = src tests


.PHONY: prepare
prepare:
	poetry install


.PHONY: lintable
lintable: prepare
	poetry run black $(sources)
	poetry run ruff check --fix $(sources)


.PHONY: lintable-docs
lintable-docs: prepare
	poetry run python -m pytest tests/test_docs.py --update-examples


.PHONY: lint
lint: prepare
	poetry check
	poetry run black --check --diff $(sources)
	poetry run ruff check $(sources)
	poetry run mypy $(sources)


.PHONY: test
test: prepare
	poetry run coverage run -m pytest
	poetry run coverage report


.PHONY: doctest
doctest: prepare
	poetry run python -m pytest tests/test_docs.py


# Test specific (earlier) versions of dependencies
.PHONY: test-dep-versions
test-dep-versions: prepare
	poetry run pip install pydantic==2.6.0
	poetry run python -m pytest


.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]'`
	rm -f `find . -type f -name '*~'`
	rm -f `find . -type f -name '.*~'`
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist
	rm -rf coverage.xml


.PHONY: package
package: prepare
	poetry build


.PHONY: help
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-19s\033[0m %s\n", $$2, $$3}'
