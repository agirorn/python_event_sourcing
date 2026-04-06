.PHONY: dev
dev:
	yardman \
		Makefile \
		pyproject.toml \
		'src/*.py' \
		'src/**/*.py' \
		'tests/*.py' \
		'**/*.py' \
		'./tests/**/*.py' \
		'make dev-exec'

.PHONY: dev-exec
dev-exec:
	@clear
	@echo "dev exec"
	@line-cli
	@make test
	@line-cli
	@make ruff-check
	@line-cli
	@make pyright
	@line-cli
	@make format-check

.PHONY: test
test:
	make test-unit

.PHONY: test-unit
test-unit:
	# uv run pytest tests/unit
	uv run pytest tests/unit

.PHONY: lint
lint:
	make pyright
	make ruff-check
	make format-check

.PHONY: pyright
pyright:
	cd ../../.. && uv run pyright packages/pip/event_sourced

.PHONY: ruff-check
ruff-check:
	cd ../../.. && uv run ruff check packages/pip/event_sourced

.PHONY: ruff-format
ruff-format:
	uv run ruff format .

.PHONY: format-check
format-check:
	uv run ruff format --check .
