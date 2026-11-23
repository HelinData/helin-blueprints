ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: test token register build publish

test:
	cd module && poetry install --no-root && poetry run pytest

token:
	./scripts/get-token.sh

register:
	./scripts/register.sh

build:
	docker build -t pipeline-observability:local ./module

publish:
	./scripts/build-and-publish.sh $(VERSION)
