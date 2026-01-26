# daggerverse

Monorepo with small, self-contained projects. This README documents the
`esp-adf-docker` and `esp-idf` projects. The `flutter` folder is currently
undocumented.

## esp-adf-docker

Builds an ESP-ADF (Espressif Audio Development Framework) Docker image on top
of Espressif's official ESP-IDF image.

### What it builds

- Base image: `espressif/idf:${IDF_RELEASE}`
- ESP-ADF repo: `https://github.com/espressif/esp-adf.git` at `ADF_RELEASE`
- Entry point: sources `$ADF_PATH/export.sh` then execs the command

### esp-adf-docker files

- `esp-adf-docker/Dockerfile` — build recipe and version pins.
- `esp-adf-docker/entrypoint.sh` — sources ESP-ADF env.
- `esp-adf-docker/dagger/` — Dagger module for build/publish.

### Versions and tag format

- `IDF_RELEASE` and `ADF_RELEASE` are set in `esp-adf-docker/Dockerfile`.
- Published image tag is:
  `adf-<ADF_RELEASE>-idf-<IDF_RELEASE>`

### Build locally

```bash
docker build -t esp-adf:local esp-adf-docker
```

### Run locally

```bash
docker run --rm -it esp-adf:local /bin/bash
```

### Publish with Dagger

The Dagger module lives in `esp-adf-docker/dagger` and targets Dagger
`v0.12.7` (see `esp-adf-docker/dagger.json`).

From `esp-adf-docker`:

```bash
dagger call publish --src . --token file:.docker-token
```

Expected tag format:
`docker.io/<username>/esp-adf:adf-<ADF_RELEASE>-idf-<IDF_RELEASE>`

### Secrets

- Docker PAT is passed as a Dagger secret.
- `.docker-token` is ignored by git (see `esp-adf-docker/.gitignore`).

## esp-idf

Dagger module for running `idf.py` using either the official ESP-IDF image or
an ESP-ADF image.

### esp-idf files

- `esp-idf/src/main/esp_idf.py` — Dagger module implementation.
- `esp-idf/src/main/resources/run_esp_rfc2217_server.py` — RFC2217 helper.

### Usage

List functions:

```bash
dagger functions
```

Run a build:

```bash
dagger call run --project-dir . --idf-version v5.1 --idf-args build
```

Menuconfig (interactive):

```bash
dagger call config --project-dir .
```

Flash (RFC2217):

```bash
dagger call flash --project-dir . --serial-host host.docker.internal --serial-port 4000
```

### Notes

- `adf_version` is optional. If set, it may be either an image tag (e.g.
  `adf-v2.7-idf-v5.3.1`) or a full image reference
  (e.g. `alanmosely/esp-adf:adf-v2.7-idf-v5.3.1`).
- `config` runs `idf.py menuconfig`, which is interactive and requests a TTY.
- `flash` connects to a host RFC2217 server. You can override host and port.

### RFC2217 helper (Windows)

The helper script is Windows-only and requires `pyserial`:

```bash
pip install pyserial
python esp-idf/src/main/resources/run_esp_rfc2217_server.py
```

If `esp_rfc2217_server.exe` is not present, it will be downloaded from the
latest esptool GitHub release.

### Development

```bash
dagger develop --sdk python
```

## Release automation

Repo-level Dagger module to create GitHub releases.

From repo root:

```bash
dagger call release-module --module esp-idf --version v0.0.4 --token env:GITHUB_TOKEN
```

This creates a GitHub release for tag `esp-idf/v0.0.4` with auto-generated
release notes.
