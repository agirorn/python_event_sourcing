.PHONY: start
start:
	pnpm exec pge start --user admin --password admin app_dev app_test

.PHONY: stop
stop:
	kill -9 $(lsof -t -i:5432)

.PHONY: clean
clean:
	rm -rf .pg-data

.PHONY: clean-all
clean-all:
	rm -rf .pg-data
	rm -rf node_modules/

.PHONY: setup
setup:
	pnpm install
