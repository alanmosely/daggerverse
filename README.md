# daggerverse

Monorepo with small, self-contained projects. This README documents the
`esp-adf-docker` and `esp-idf` projects.

## Requirements

- Dagger CLI `v0.21.8` or later — all modules pin `engineVersion: v0.21.8`
  in their `dagger.json` (install per <https://docs.dagger.io/install>).
- A running container runtime (e.g. Docker) for the Dagger engine.
- Python 3 with esptool >= 5.0 only if you use the RFC2217 flash helper.

## CI

GitHub Actions (`.github/workflows/`):

- `ci.yml` — on every push/PR: ruff lint, module-load checks
  (`dagger functions` plus a `dagger call <fn> --help`), and the cheap
  module self-tests (`dagger check`) for the release and esp-adf-docker
  modules; on pushes to master additionally the esp-idf self-test — a full
  hello-world firmware build with artifact assertions.
- `release.yml` — on pushing a `<module>/vX.Y.Z` tag: creates the GitHub
  release via this repo's own release module and, for `esp-idf` tags,
  verifies the tagged module loads remotely and submits it to Daggerverse.

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
- `esp-adf-docker/dagger/` — Dagger module source for build/publish (the
  module root is `esp-adf-docker/`; run `dagger` commands from there).

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

### Build and publish with Dagger

Run these from `esp-adf-docker/`. Build without publishing (returns the
built container — chain e.g. `terminal` or `platform` on it):

```bash
dagger call build --src .
```

Publish, with a Docker Hub PAT in the `DOCKERHUB_TOKEN` environment
variable:

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

The easiest way to use the module is remotely from Daggerverse, run from
your ESP-IDF firmware project's directory:

```bash
dagger call -m github.com/alanmosely/daggerverse/esp-idf build --project-dir . export --path ./build
```

Pin a version by appending `@esp-idf/vX.Y.Z` to the module ref, or add it
as a dependency of your own module with
`dagger install github.com/alanmosely/daggerverse/esp-idf`.

With a local checkout, run from `esp-idf/` (where the module's
`dagger.json` lives) and point `--project-dir` at your firmware project —
note that `--project-dir .` would mount the module directory itself, which
is not an ESP-IDF project. Running `dagger functions` from the repo root
lists the repo-level release module instead of this one.

List functions (from `esp-idf/`):

```bash
dagger functions
```

Run an arbitrary idf.py command (defaults to `build`):

```bash
dagger call run --project-dir <your-project> --idf-args build
```

Build and export the artifacts (bootloader, partition table, app binary):

```bash
dagger call build --project-dir <your-project> export --path ./build
```

Menuconfig (interactive) and export the resulting `sdkconfig`:

```bash
dagger call config --project-dir <your-project> export --path ./sdkconfig
```

Show the size report (`--components` for per-component sizes):

```bash
dagger call size --project-dir <your-project>
```

Render the project docs (official IDF image only; no `--adf-version` or
`--target` support):

```bash
dagger call docs --project-dir <your-project>
```

Flash (RFC2217):

```bash
dagger call flash --project-dir <your-project> --serial-host host.docker.internal --serial-port 4000
```

### Notes

- `idf_version` selects the `espressif/idf` image tag and defaults to
  `v5.1`; it is ignored entirely when `adf_version` is set.
- `adf_version` is optional. If set, it may be either an image tag (e.g.
  `adf-v2.7-idf-v5.3.4`) or a full image reference
  (e.g. `alanmosely/esp-adf:adf-v2.7-idf-v5.3.4`). Bare tags (no `/`)
  resolve against `alanmosely/esp-adf` by default; override with the
  `--adf-image-repo` module constructor argument.
- `config` runs `idf.py menuconfig` interactively (requires a TTY) and returns
  the resulting `sdkconfig` as a file. Container filesystem changes are not
  written back to the host, so use `export --path ./sdkconfig` to save it.
  It runs `idf.py fullclean` before menuconfig within its own session (this
  does not affect later builds, which mount the project fresh).
- `build` returns the `build/` directory; use `export --path ./build` to
  retrieve the artifacts.
- `flash` builds and flashes via a host RFC2217 server. You can override host
  and port, and pass `--clean` to run `fullclean` first.
- Pass `--target esp32s3` (etc.) to `run`, `build`, `config`, `size`, or
  `flash` to run `idf.py set-target` first.
- Compilation uses ccache backed by a shared Dagger cache volume
  (`esp-idf-ccache`), so warm rebuilds are much faster.

### RFC2217 helper

The helper script works on Windows, Linux, and macOS. It requires
esptool >= 5.0, which provides the `esp_rfc2217_server` command and
`pyserial`:

```bash
pip install "esptool>=5.0"
python esp-idf/src/main/resources/run_esp_rfc2217_server.py
```

It auto-detects the connected ESP device's serial port by USB VID/PID (an
ESP board must be plugged in; pass the port explicitly to skip detection,
e.g. `run_esp_rfc2217_server.py COM3`), then serves it in the foreground on
TCP port 4000 — matching `flash`'s default
`--serial-host host.docker.internal --serial-port 4000`. Override the TCP
port with `--tcp-port`.

### Development

From `esp-idf/`: edit `src/main/esp_idf.py`, then run `dagger develop` to
regenerate the `sdk/` bindings. Verify with `dagger functions` and
`dagger call <function> --help`, then run the module's self-test with
`dagger check` — it builds a hello-world firmware project and verifies the
artifacts. All three modules define such self-tests as Dagger checks
(`dagger check -l` lists them).

```bash
dagger develop
```

### Publish to Daggerverse

1) Pick the next version above the highest existing `esp-idf/*` tag
(`git tag --list "esp-idf/*"`) and set it (without the `v`) in
`esp-idf/pyproject.toml`.

2) Commit, tag, and push (master and the tag):

```bash
git add esp-idf/pyproject.toml
git commit -m "esp-idf: bump version to vX.Y.Z"
git tag esp-idf/vX.Y.Z
git push origin master esp-idf/vX.Y.Z
```

Pushing the tag triggers the Release workflow
(`.github/workflows/release.yml`), which creates the GitHub release and
submits the module to Daggerverse automatically — steps 3 and 4 below are
the pre-push sanity check and the manual fallback.

3) Verify the tag points at `HEAD` and the repo is clean:

```bash
git rev-parse HEAD
git rev-parse esp-idf/vX.Y.Z
git status
```

4) Manual fallback publish. The `dagger publish` command no longer exists;
Daggerverse publishes modules from public git tags. Either submit the module at
<https://daggerverse.dev/publish>, or trigger auto-publish by using the
module remotely:

```bash
dagger functions -m github.com/alanmosely/daggerverse/esp-idf@esp-idf/vX.Y.Z
```

## Release automation

Repo-level Dagger module to create GitHub releases. The token needs the
`repo` scope (classic) or Contents read/write (fine-grained).

The Release workflow runs this automatically when a `<module>/vX.Y.Z` tag
is pushed. To run it manually from the repo root:

```bash
dagger call release-module --module esp-idf --version vX.Y.Z --token env:GITHUB_TOKEN
```

This creates a GitHub release for tag `esp-idf/vX.Y.Z` with auto-generated
release notes. A generic `release --tag <tag>` function is also available.
Both default to repo `alanmosely/daggerverse` and auto-generated notes;
override with `--repo owner/name`, `--draft`, `--prerelease`,
`--target <commitish>`, or `--generate-notes=false --body '...'`.
