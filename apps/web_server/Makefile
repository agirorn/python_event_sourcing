.PHONY: start
start:
	uv run uvicorn web_server.main:app --reload

.PHONY: http-get-root
http-get-root:
	curl -X GET http://127.0.0.1:8000/

.PHONY: http-post-hello
http-post-hello:
	curl -X POST http://127.0.0.1:8000/hello \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice"}'
