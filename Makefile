
compose-build:
	docker compose -f docker/compose.yaml -p absurdly-goud build

compose-up:
	docker compose -f docker/compose.yaml -p absurdly-goud up

compose-rebuild:
	docker compose -f docker/compose.yaml -p absurdly-goud down -v
	docker compose -f docker/compose.yaml -p absurdly-goud up -d --build

obsidian-to-jekyll:
	python -m scripts.obsidian_to_jekyll --vault .\absurdly-goud-obsidian\
