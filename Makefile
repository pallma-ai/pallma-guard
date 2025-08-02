.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  install-all - Install all dependencies"
	@echo "  install-cli - Install CLI dependencies"
	@echo "  install-sdk - Install SDK dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo "  lint - Run linting"

.PHONY: install-all
install-all:
	uv sync --group all

.PHONY: install-cli
install-cli:
	uv sync --group cli

.PHONY: install-sdk
install-sdk:
	uv sync --group sdk

.PHONY: install-dev
install-dev:
	uv sync --group dev

.PHONY: lint
lint:
	uv run ruff check .

