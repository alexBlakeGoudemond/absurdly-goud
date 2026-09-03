
compose-build:
	docker compose -f docker/compose.yaml -p absurdly-goud build

compose-up:
	docker compose -f docker/compose.yaml -p absurdly-goud up

compose-rebuild-no-cache:
	powershell -Command "if (Test-Path .\site_src) { Remove-Item .\site_src -Recurse -Force }"
	powershell -Command "if (Test-Path .\_site) { Remove-Item .\_site -Recurse -Force }"
	docker compose -f docker/compose.yaml -p absurdly-goud down -v
	docker compose -f docker/compose.yaml -p absurdly-goud up -d --build

compose-rebuild-cache:
	docker compose -f docker/compose.yaml -p absurdly-goud down -v
	docker compose -f docker/compose.yaml -p absurdly-goud up -d --build

obsidian-to-jekyll:
	python -m scripts.obsidian_to_jekyll --vault .\absurdly-goud-obsidian\
