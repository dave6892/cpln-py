.PHONY: clean lint format test docs build install dev-install

SHELL = /bin/bash

default: help

help:
	@echo "Available commands:"
	@echo "  clean        - Remove build artifacts and cache directories"
	@echo "  lint         - Run linting tools (ruff, mypy)"
	@echo "  format       - Format code with ruff"
	@echo "  test         - Run tests with pytest"
	@echo "  docs         - Build documentation"
	@echo "  build        - Build the package"
	@echo "  install      - Install the package"
	@echo "  dev-install  - Install the package in development mode with all dependencies"

clean:
	find . -path ".pdm-build" -type d -prune -exec rm -rf {} +
	find . -path "dist" -type d -prune -exec rm -rf {} +
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.egg-info" -type d -prune -exec rm -rf {} +
	find . -name "*_version.py" -type f -delete
	find . -name ".coverage" -type f -delete
	find . -name ".pytest_cache" -type d -prune -exec rm -rf {} +
	find . -name ".ruff_cache" -type d -prune -exec rm -rf {} +
	find . -name ".mypy_cache" -type d -prune -exec rm -rf {} +

lint:
	pdm run ruff check .
	pdm run mypy src/cpln

format:
	pdm run ruff format .

test:
	pdm run pytest

docs:
	pdm run mkdocs build && pdm run mkdocs serve

build: clean
	pdm build

install: build
	pdm install --prod

dev-install:
	pdm install -G dev
