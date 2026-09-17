
# ----------------------------------
# Local Dev commands below
# ----------------------------------

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

# ----------------------------------
# Webmention.io commands below
# ----------------------------------

webmentions_io_fetch_all:
	python .\scripts\webmention\webmention_pull.py --from 2026-09-15 --env-file .env/webmentions.io.env --target-guestbook-pattern https://absurdlygoud.com/guestbook/
