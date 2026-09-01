from datetime import datetime, timezone
from typing import Annotated

import dagger
from dagger import dag, Doc, function, object_type

DEFAULT_IMAGE_VERSION = "v5.1"


@object_type
class EspIdf:
    def _idf_container(
        self,
        project_dir: dagger.Directory,
        adf_version: str | None,
        idf_version: str,
    ) -> dagger.Container:
        """Helper to create a container with the project mounted at /project"""
        if adf_version:
            image_ref = (
                adf_version
                if "/" in adf_version
                else f"alanmosely/esp-adf:{adf_version}"
            )
        else:
            image_ref = f"espressif/idf:{idf_version}"

        return (
            dag.container()
            .from_(image_ref)
            .with_mounted_directory("/project", project_dir)
            .with_workdir("/project")
        )

    async def _execute_idf_command(
        self,
        project_dir: dagger.Directory,
        adf_version: str | None,
        idf_version: str,
        idf_args: list[str],
    ) -> str:
        """Helper function to execute idf.py commands"""
        return await (
            self._idf_container(project_dir, adf_version, idf_version)
            .with_exec(["idf.py", *idf_args], use_entrypoint=True)
            .stdout()
        )

    @function
    async def run(
        self,
        project_dir: Annotated[
            dagger.Directory, Doc("The directory containing the ESP-IDF project")
        ],
        adf_version: Annotated[
            str | None,
            Doc(
                "The Espressif ADF image tag or full image reference to use; if set, idf_version is ignored"
            ),
        ] = None,
        idf_version: Annotated[
            str, Doc("The version of the Espressif IDF Docker image to use")
        ] = DEFAULT_IMAGE_VERSION,
        idf_args: Annotated[
            list[str] | None, Doc("The arguments to pass to idf.py")
        ] = None,
    ) -> str:
        """Execute idf.py from the Espressif IDF or ADF Docker image, by default building the project"""
        if idf_args is None:
            idf_args = ["build"]
        return await self._execute_idf_command(
            project_dir, adf_version, idf_version, idf_args
        )

    @function
    def build(
        self,
        project_dir: Annotated[
            dagger.Directory, Doc("The directory containing the ESP-IDF project")
        ],
        adf_version: Annotated[
            str | None,
            Doc(
                "The Espressif ADF image tag or full image reference to use; if set, idf_version is ignored"
            ),
        ] = None,
        idf_version: Annotated[
            str, Doc("The version of the Espressif IDF Docker image to use")
        ] = DEFAULT_IMAGE_VERSION,
    ) -> dagger.Directory:
        """Execute "idf.py build" and return the build output directory

        Export the artifacts locally with:
        dagger call build --project-dir . export --path ./build
        """
        return (
            self._idf_container(project_dir, adf_version, idf_version)
            .with_exec(["idf.py", "build"], use_entrypoint=True)
            .directory("/project/build")
        )

    @function
    def config(
        self,
        project_dir: Annotated[
            dagger.Directory, Doc("The directory containing the ESP-IDF project")
        ],
        adf_version: Annotated[
            str | None,
            Doc(
                "The Espressif ADF image tag or full image reference to use; if set, idf_version is ignored"
            ),
        ] = None,
        idf_version: Annotated[
            str, Doc("The version of the Espressif IDF Docker image to use")
        ] = DEFAULT_IMAGE_VERSION,
    ) -> dagger.File:
        """Execute "idf.py menuconfig" interactively and return the resulting sdkconfig

        Requires a TTY (run via "dagger call" in a terminal). Dagger terminal
        sessions are ephemeral, so the saved sdkconfig is staged on a cache
        volume and returned as a file. Export it back into your project with:
        dagger call config --project-dir . export --path ./sdkconfig
        """
        staging = dag.cache_volume("esp-idf-menuconfig")
        return (
            self._idf_container(project_dir, adf_version, idf_version)
            .with_mounted_cache("/staging", staging)
            .with_exec(["idf.py", "fullclean"], use_entrypoint=True)
            .terminal(
                cmd=[
                    "/bin/bash",
                    "-c",
                    "rm -f /staging/sdkconfig"
                    " && . $IDF_PATH/export.sh"
                    " && idf.py menuconfig"
                    " && cp sdkconfig /staging/sdkconfig",
                ]
            )
            # cache volume contents are not part of Dagger's cache key, so
            # force the copy below to re-run on every call
            .with_env_variable(
                "CACHE_BUSTER", datetime.now(timezone.utc).isoformat()
            )
            .with_exec(["cp", "/staging/sdkconfig", "/sdkconfig"])
            .file("/sdkconfig")
        )

    @function
    async def docs(
        self,
        project_dir: Annotated[
            dagger.Directory, Doc("The directory containing the ESP-IDF project")
        ],
        idf_version: Annotated[
            str, Doc("The version of the Espressif IDF Docker image to use")
        ] = DEFAULT_IMAGE_VERSION,
    ) -> str:
        """Execute "idf.py docs" from the official Espressif IDF Docker image"""
        return await self._execute_idf_command(project_dir, None, idf_version, ["docs"])

    @function
    async def flash(
        self,
        project_dir: Annotated[
            dagger.Directory, Doc("The directory containing the ESP-IDF project")
        ],
        adf_version: Annotated[
            str | None,
            Doc(
                "The Espressif ADF image tag or full image reference to use; if set, idf_version is ignored"
            ),
        ] = None,
        idf_version: Annotated[
            str, Doc("The version of the Espressif IDF Docker image to use")
        ] = DEFAULT_IMAGE_VERSION,
        serial_host: Annotated[
            str, Doc("RFC2217 host for serial forwarding")
        ] = "host.docker.internal",
        serial_port: Annotated[
            int, Doc("RFC2217 port for serial forwarding")
        ] = 4000,
    ) -> str:
        """Execute "idf.py flash" from the official Espressif IDF or ADF Docker image using the rfc2217 protocol to connect to the host machine's serial port"""
        print(
            "\nRequires esp_rfc2217_server to be running, to set this up, download and run: https://raw.githubusercontent.com/alanmosely/daggerverse/refs/heads/master/esp-idf/src/main/resources/run_esp_rfc2217_server.py"
        )
        print(
            f"\nThis will start a server on port {serial_port} that will forward serial port data to the container, see: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/tools/idf-docker-image.html#using-remote-serial-port\n"
        )
        return await self._execute_idf_command(
            project_dir,
            adf_version,
            idf_version,
            [
                "--port",
                f"rfc2217://{serial_host}:{serial_port}?ign_set_control",
                "fullclean",
                "build",
                "flash",
            ],
        )
