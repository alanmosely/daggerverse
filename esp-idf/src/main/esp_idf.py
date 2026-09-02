from datetime import datetime, timezone
from typing import Annotated

import dagger
from dagger import Doc, check, dag, function, object_type

DEFAULT_IMAGE_VERSION = "v5.1"


@object_type
class EspIdf:
    adf_image_repo: Annotated[
        str,
        Doc("Image repository used when adf_version is a bare tag"),
    ] = "alanmosely/esp-adf"

    def _idf_container(
        self,
        project_dir: dagger.Directory,
        adf_version: str | None,
        idf_version: str,
        target: str | None = None,
    ) -> dagger.Container:
        """Helper to create a container with the project mounted at /project"""
        if adf_version:
            image_ref = (
                adf_version
                if "/" in adf_version
                else f"{self.adf_image_repo}:{adf_version}"
            )
        else:
            image_ref = f"espressif/idf:{idf_version}"

        container = (
            dag.container()
            .from_(image_ref)
            .with_env_variable("IDF_CCACHE_ENABLE", "1")
            .with_env_variable("CCACHE_DIR", "/ccache")
            .with_mounted_cache("/ccache", dag.cache_volume("esp-idf-ccache"))
            .with_mounted_directory("/project", project_dir)
            .with_workdir("/project")
        )
        if target:
            container = container.with_exec(
                ["idf.py", "set-target", target], use_entrypoint=True
            )
        return container

    async def _execute_idf_command(
        self,
        project_dir: dagger.Directory,
        adf_version: str | None,
        idf_version: str,
        idf_args: list[str],
        target: str | None = None,
    ) -> str:
        """Helper function to execute idf.py commands"""
        return await (
            self._idf_container(project_dir, adf_version, idf_version, target)
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
        target: Annotated[
            str | None,
            Doc(
                'The chip to build for, e.g. esp32s3; runs "idf.py set-target" first'
            ),
        ] = None,
    ) -> str:
        """Execute idf.py from the Espressif IDF or ADF Docker image, by default building the project"""
        if idf_args is None:
            idf_args = ["build"]
        return await self._execute_idf_command(
            project_dir, adf_version, idf_version, idf_args, target
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
        target: Annotated[
            str | None,
            Doc(
                'The chip to build for, e.g. esp32s3; runs "idf.py set-target" first'
            ),
        ] = None,
    ) -> dagger.Directory:
        """Execute "idf.py build" and return the build output directory

        Export the artifacts locally with:
        dagger call build --project-dir . export --path ./build
        """
        return (
            self._idf_container(project_dir, adf_version, idf_version, target)
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
        target: Annotated[
            str | None,
            Doc(
                'The chip to configure for, e.g. esp32s3; runs "idf.py set-target" first'
            ),
        ] = None,
    ) -> dagger.File:
        """Execute "idf.py menuconfig" interactively and return the resulting sdkconfig

        Requires a TTY (run via "dagger call" in a terminal). Dagger terminal
        sessions are ephemeral, so the saved sdkconfig is staged on a cache
        volume and returned as a file. Export it back into your project with:
        dagger call config --project-dir . export --path ./sdkconfig
        """
        staging = dag.cache_volume("esp-idf-menuconfig")
        return (
            self._idf_container(project_dir, adf_version, idf_version, target)
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
    async def size(
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
        target: Annotated[
            str | None,
            Doc(
                'The chip to build for, e.g. esp32s3; runs "idf.py set-target" first'
            ),
        ] = None,
        components: Annotated[
            bool, Doc('Report per-component sizes ("idf.py size-components")')
        ] = False,
    ) -> str:
        """Execute "idf.py size" (or "size-components") and return the size report

        Builds the project first if needed (size reads the linker map file).
        """
        return await self._execute_idf_command(
            project_dir,
            adf_version,
            idf_version,
            ["size-components" if components else "size"],
            target,
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
        clean: Annotated[
            bool, Doc("Run 'idf.py fullclean' before building")
        ] = False,
        target: Annotated[
            str | None,
            Doc(
                'The chip to build for, e.g. esp32s3; runs "idf.py set-target" first'
            ),
        ] = None,
    ) -> str:
        """Execute "idf.py flash" from the official Espressif IDF or ADF Docker image using the rfc2217 protocol to connect to the host machine's serial port

        Requires an RFC2217 server running on the host that forwards the
        device's serial port. Cross-platform helper (needs esptool >= 5.0):
        https://raw.githubusercontent.com/alanmosely/daggerverse/refs/heads/master/esp-idf/src/main/resources/run_esp_rfc2217_server.py
        See:
        https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/tools/idf-docker-image.html#using-remote-serial-port
        """
        idf_args = [
            "--port",
            f"rfc2217://{serial_host}:{serial_port}?ign_set_control",
        ]
        if clean:
            idf_args.append("fullclean")
        idf_args += ["build", "flash"]
        return await self._execute_idf_command(
            project_dir, adf_version, idf_version, idf_args, target
        )

    @function
    @check
    async def check_build(self) -> None:
        """Self-test: build a minimal hello-world project and verify the artifacts"""
        project = (
            dag.directory()
            .with_new_file(
                "CMakeLists.txt",
                "cmake_minimum_required(VERSION 3.16)\n"
                "include($ENV{IDF_PATH}/tools/cmake/project.cmake)\n"
                "project(hello_world)\n",
            )
            .with_new_file(
                "main/CMakeLists.txt",
                'idf_component_register(SRCS "hello_world_main.c" INCLUDE_DIRS "")\n',
            )
            .with_new_file(
                "main/hello_world_main.c",
                '#include <stdio.h>\nvoid app_main(void) { printf("Hello world!\\n"); }\n',
            )
        )
        build_dir = self.build(project, target="esp32")
        entries = await build_dir.entries()
        missing = [
            name
            for name in ("hello_world.bin", "hello_world.elf")
            if name not in entries
        ]
        if missing:
            raise ValueError(
                f"build artifacts missing: {missing}; build dir contains: {entries}"
            )
        bootloader = await build_dir.directory("bootloader").entries()
        if "bootloader.bin" not in bootloader:
            raise ValueError(
                f"bootloader.bin missing; bootloader dir contains: {bootloader}"
            )
