
compose-build:
	docker compose -f docker/compose.yaml -p absurdly-goud build

compose-up:
	docker compose -f docker/compose.yaml -p absurdly-goud up -d

