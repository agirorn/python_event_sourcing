.PHONY: setup
setup:
	uv sync --dev
	cd tools/pg && make setup
	uv sync --dev --all-packages

.PHONY: start-web
start:
	mprocs

.PHONY: start-web
start-web:
	cd apps/web_server && make start

.PHONY: stop
stop:
	@kill -9 $(lsof -ti:8000) > /dev/null 2>&1; echo ""

.PHONY: restart
restart:
	sleep 1 && make stop && sleep 1 && make start

.PHONY: ruff-check
ruff-check:
	uv run ruff check .

.PHONY: format
format:
	uv run ruff check --fix
	uv run ruff format .

.PHONY: format-check
format-check:
	uv run ruff format . --check

.PHONY: pyright
pyright:
	@# sync all packages to skipt getting even not ready errors
	uv sync --dev --all-packages
	uv run pyright

.PHONY: basedpyright
basedpyright:
	uv run basedpyright

.PHONY: pytest
pytest:
	uv run pyright

.PHONY: clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} \; ; echo "DONE"
	cd tools/pg && make clean

.PHONY: clean-all
clean-all:
	make clean
	rm uv.lock
	rm -rf .venv

.PHONY: http-get-root
http-get-root:
	cd apps/web_server && make http-get-root

.PHONY: http-post-hello
http-post-hello:
	cd apps/web_server && make http-post-hello

lint:
	make pyright
	make ruff-check
	make format-check

.PHONY: test
test:
	make pytest


.PHONY: dev
dev:
	yardman \
		'Makefile' \
		'**/Makefile' \
		'pyproject.toml' \
		'**/pyproject.toml' \
		'*.py' \
		'**/*.py' \
		'make dev-exec'

.PHONY: dev-exec
dev-exec:
	clear
	make test
	@echo "----------------------------------"
	make lint

.PHONY: list-versions
list-versions:
	uv run  import_version.py

.PHONY: start-doc-all
start-doc-all:
	 uv run --with pdoc -- pdoc `uv pip freeze | cut -d= -f1` `uv run python -c "import sys; print(' '.join(sorted(sys.stdlib_module_names)))"`

.PHONY: start-doc-dependecies
start-doc-dependecies:
	 uv run --with pdoc -- pdoc `uv pip freeze | rg -v 'ruff|pyright' | cut -d= -f1`

.PHONY: start-doc-std-lib
start-doc-std-lib:
	 uv run --with pdoc -- pdoc `uv run python -c "import sys; print(' '.join(sorted(sys.stdlib_module_names)))"`

.PHONY: start-db
start-db:
	cd tools/pg && make start

.PHONY: db-migrate
db-migrate:
	cd packages/pip/event_store_pg \
		&& pgmt migrate \
			--url "postgresql://admin:admin@localhost:5432/app_test" \
			migrations
