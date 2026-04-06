.PHONY: dev
dev:
	yardman \
		Makefile \
		'src/*.py' \
		'src/**/*.py' \
		'make dev-exec'

.PHONY: dev-exec
dev-exec:
	clear
	echo "dev exec"
	make test

.PHONY: test
test:
	make test-unit

.PHONY: test-unit
test-unit:
	uv run
