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
`v0.21.8` (see `esp-adf-docker/dagger.json`).

From `esp-adf-docker`, with a Docker Hub PAT in the `DOCKERHUB_TOKEN`
environment variable:

```bash
dagger call publish --src . --token env:DOCKERHUB_TOKEN
```

Expected tag format:
`docker.io/<username>/esp-adf:adf-<ADF_RELEASE>-idf-<IDF_RELEASE>`

Registry and username default to `docker.io`/`alanmosely` and can be
overridden as module constructor arguments:

```bash
dagger call --registry=ghcr.io --username=you publish --src . --token env:DOCKERHUB_TOKEN
```

### Secrets

- Docker PAT is passed as a Dagger secret from the environment
  (`env:DOCKERHUB_TOKEN`); avoid writing tokens to files.

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

Build and export the artifacts (bootloader, partition table, app binary):

```bash
dagger call build --project-dir . export --path ./build
```

Menuconfig (interactive) and export the resulting `sdkconfig`:

```bash
dagger call config --project-dir . export --path ./sdkconfig
```

Flash (RFC2217):

```bash
dagger call flash --project-dir . --serial-host host.docker.internal --serial-port 4000
```

### Notes

- `adf_version` is optional. If set, it may be either an image tag (e.g.
  `adf-v2.7-idf-v5.3.1`) or a full image reference
  (e.g. `alanmosely/esp-adf:adf-v2.7-idf-v5.3.1`). Bare tags resolve against
  `alanmosely/esp-adf` by default; override with the `--adf-image-repo`
  module constructor argument.
- `config` runs `idf.py menuconfig` interactively (requires a TTY) and returns
  the resulting `sdkconfig` as a file. Container filesystem changes are not
  written back to the host, so use `export --path ./sdkconfig` to save it.
- `build` returns the `build/` directory; use `export --path ./build` to
  retrieve the artifacts.
- `flash` builds and flashes via a host RFC2217 server. You can override host
  and port, and pass `--clean` to run `fullclean` first.
- Pass `--target esp32s3` (etc.) to `run`, `build`, `config`, or `flash` to
  run `idf.py set-target` first.
- Compilation uses ccache backed by a shared Dagger cache volume
  (`esp-idf-ccache`), so warm rebuilds are much faster.

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

### Publish to Daggerverse

1) Bump the version in `esp-idf/pyproject.toml`.

2) Commit, tag, and push the tag:

```bash
git add esp-idf/pyproject.toml
git commit -m "esp-idf: bump version to v0.0.4"
git tag esp-idf/v0.0.4
git push origin esp-idf/v0.0.4
```

3) Verify the tag points at `HEAD` and the repo is clean:

```bash
git rev-parse HEAD
git rev-parse esp-idf/v0.0.4
git status
```

4) Publish the module (from the module directory):

```bash
cd esp-idf
dagger publish
```

If you publish with `--force`, Daggerverse will use the commit SHA instead of
the tag. To publish a versioned release, keep the repo clean.

## Release automation

Repo-level Dagger module to create GitHub releases.

From repo root:

```bash
dagger call release-module --module esp-idf --version v0.0.4 --token env:GITHUB_TOKEN
```

This creates a GitHub release for tag `esp-idf/v0.0.4` with auto-generated
release notes.
