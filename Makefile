# Форматирование и линтинг кода
lint-backend:
	cd app && uv run ruff check --fix --show-fixes

format-backend:
	cd app && uv run ruff format .

laf: lint-backend format-backend
	@echo [-- All checks passed, code formatted --]