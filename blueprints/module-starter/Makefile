ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: token register build

token:
	./scripts/get-token.sh

register:
	./scripts/register.sh

build:
	docker build -t sample-module:local ./module
