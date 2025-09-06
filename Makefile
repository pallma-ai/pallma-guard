.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  install-all - Install all dependencies"
	@echo "  install-cli - Install CLI dependencies"
	@echo "  install-sdk - Install SDK dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo "  lint - Run linting checks"
	@echo "  lint-fix - Run linting and auto-fix issues"
	@echo "  format - Format code with ruff"
	@echo "  format-check - Check if code is properly formatted"
	@echo "  check - Run linting and format checks"
	@echo "  check-fix - Run linting and formatting with auto-fix"

.PHONY: install
install:
	uv sync

.PHONY: install-sdk
install-sdk:
	uv sync --extra sdk

.PHONY: install-dev
install-dev:
	uv sync --group dev

.PHONY: lint
lint:
	uv run ruff check .

.PHONY: lint-fix
lint-fix:
	uv run ruff check --fix .

.PHONY: format
format:
	uv run ruff format .

.PHONY: format-check
format-check:
	uv run ruff format --check .

.PHONY: check
check: lint format-check
	@echo "All checks passed!"

.PHONY: check-fix
check-fix: lint-fix format
	@echo "All issues fixed!"

.PHONY: bump-version
bump-version:
	@:$(if $(version),,$(error version is not set. Run make bump-version version=patch or version=minor or version=major))
	uv run --no-sync bump2version $(version)
