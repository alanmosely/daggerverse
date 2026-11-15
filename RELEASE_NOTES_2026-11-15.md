# ESP-IDF 0.0.7 and ESP-ADF Docker 0.0.1

## ESP-IDF module upgrade

Pin the module to
`github.com/alanmosely/daggerverse/esp-idf@esp-idf/v0.0.7`, or update the
equivalent dependency in your consuming module and run `dagger develop`.
For example, from an ESP-IDF project:

```sh
dagger call -m github.com/alanmosely/daggerverse/esp-idf@esp-idf/v0.0.7 config --project-dir . export --path ./sdkconfig
```

Each menuconfig invocation now stages and consumes its own sdkconfig. Overlapping
projects cannot export each other's results; an aborted session cannot reuse a
previous result. Save/back up your project sdkconfig before editing. The CLI
signature, Dagger 0.21.8 engine pin and default IDF image are unchanged. No
firmware or device upgrade is implied by updating this build module.

## ESP-ADF Docker module upgrade

Pin the builder to
`github.com/alanmosely/daggerverse/esp-adf-docker@esp-adf-docker/v0.0.1`.
Its recipe selects ADF v2.8 and IDF v5.5.5 with verified source commits,
submodules, the required FreeRTOS patch, QEMU and retained OS/Python inventories.

The release's newly built image uses the separate tag
`alanmosely/esp-adf:adf-v2.8-idf-v5.5.5-r1`. Use the manifest digest in the attached
image receipt for reproducible builds. Existing published tags and consumer
digests are preserved. Compare your build profiles, patch requirements, binary
sizes and hardware behavior before adopting the image in a product; physical
audio/provisioning/OTA qualification is not established by its hello-world build.

## Artifacts and validation

Dagger modules are distributed as versioned Git source, not standalone binaries.
Each release includes its module source bundle and checksums. The ADF release
also identifies its built container image and build/provenance verification.
Hosted checks validate lint, all module signatures/self-tests, the real ADF image
and ESP32 hello-world. Pinned-engine overlap and abort checks passed locally.
The deferred Dagger-engine and public IDF-default upgrades remain separate.
