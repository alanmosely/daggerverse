# Agent Notes for daggerverse

Use this as a quick ramp-up for changes in this repo. It covers the
`esp-adf-docker` and `esp-idf` projects (the documented tooling).

## Repo layout

- `esp-adf-docker/` — ESP-ADF Docker image + Dagger module.
- `esp-idf/` — Dagger module for ESP-IDF idf.py workflows.
- `dagger/` — repo-level Dagger module for GitHub releases.

## esp-adf-docker essentials

- **Purpose**: build and publish an ESP-ADF image based on `espressif/idf`.
- **Version pins** live in `esp-adf-docker/Dockerfile` as `IDF_RELEASE` and
  `ADF_RELEASE`. Keep them compatible with the ESP-ADF README matrix.
- **Entry point** sources `$ADF_PATH/export.sh` so the toolchain is ready
  for interactive shells and CI commands.

## Dagger module

- Location: `esp-adf-docker/dagger/`
- API: `build(src)` and `publish(src, token, registry, username)`
- Publish tag format: `adf-<ADF_RELEASE>-idf-<IDF_RELEASE>`
- Dockerfile is read from `src` relative path (`Dockerfile`).

### esp-adf-docker flows

Build only:

```bash
dagger call build --src .
```

Publish:

```bash
dagger call publish --src . --token file:.docker-token
```

## Conventions and gotchas

- If you change `IDF_RELEASE` or `ADF_RELEASE`, keep the publish tag format
  in sync and update docs.
- Dockerfile uses a shallow clone for speed; avoid removing it unless you
  need full history.
- Keep `entrypoint.sh` minimal; it is run for every container invocation.
- `.docker-token` is intentionally git-ignored.

## How to validate changes

- `docker build -t esp-adf:test esp-adf-docker`
- `docker run --rm -it esp-adf:test /bin/bash`

## If you expand documentation

- Prefer updating docs at repo root.
- Note any new tags, env vars, or breaking changes.

## Release automation

- Location: `dagger/src/main/release.py`
- API: `release(tag, ...)` and `release_module(module, version, ...)`
- Uses GitHub API to create releases and optional auto-generated notes.

### Typical flow

```bash
dagger call release-module --module esp-idf --version v0.0.4 --token env:GITHUB_TOKEN
```

## esp-idf essentials

- **Purpose**: run `idf.py` via Dagger using either ESP-IDF or ESP-ADF images.
- **Default image** is `espressif/idf:${DEFAULT_IMAGE_VERSION}` in
  `esp-idf/src/main/esp_idf.py`.
- **ADF image** can be provided as a tag (`adf-v2.7-idf-v5.3.1`) or a full
  image reference (`alanmosely/esp-adf:adf-v2.7-idf-v5.3.1`).

## esp-idf module

- Location: `esp-idf/src/main/esp_idf.py`
- API: `run`, `config`, `docs`, `flash`
- `config` runs `idf.py menuconfig` and uses a TTY by default.
- `flash` connects to RFC2217 on `serial_host`/`serial_port`.

### esp-idf flows

Build:

```bash
dagger call run --project-dir . --idf-version v5.1 --idf-args build
```

Menuconfig:

```bash
dagger call config --project-dir .
```

Flash (RFC2217):

```bash
dagger call flash --project-dir . --serial-host host.docker.internal --serial-port 4000
```

## esp-idf gotchas

- `config` is interactive; non-TTY environments may fail unless `interactive=false`.
- `flash` requires an RFC2217 server on the host. The helper script is
  Windows-only and needs `pyserial`.

## esp-idf validation

- `dagger functions`
- `dagger call run --project-dir . --idf-args build`
