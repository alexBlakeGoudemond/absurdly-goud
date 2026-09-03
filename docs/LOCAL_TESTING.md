# Local Testing

In this project, Ruby and Jekyll run inside Docker. This simulates the Github Pages environment, which is useful for
development and testing.

## Setup

- Confirm that `Makefile` is installed on your system: `make --version`
- Confirm that `Docker` is installed on your system (recommended: Docker Desktop): `docker --version`
- Confirm that `Python` is installed on your system: `python --version`
- Setup Python Virtual Environment:

```bash
python -m venv .venv 
```

```bash
.\.venv\Scripts\python.exe -m pip install Pillow
```

## Running

> NOTE: Ruby has 2 ports; 1 for hosting and the other for live reload

- Rebuild the site via one of the make scripts: `make compose-rebuild-no-cache`
- Open Docker Desktop and confirm that the `absurdly-goud` container is running
- Open the relevant localhost port in your browser to see and navigate the site!
