
compose-build:
	docker compose -f docker/compose.yaml -p absurdly-goud build

compose-up:
	docker compose -f docker/compose.yaml -p absurdly-goud up

compose-restart:
	docker compose -f docker/compose.yaml -p absurdly-goud restart

