from typing import Annotated

import dagger
from dagger import dag, Doc, function, object_type

DEFAULT_IMAGE_VERSION = "v5.1"


@object_type
class EspIdf:
    async def _execute_idf_command(
        self,
        project_dir: dagger.Directory,
        adf_version: str,
        idf_version: str,
        idf_args: list[str],
    ) -> str:
        """Helper function to execute idf.py commands"""
        dag_container = dag.container()

        if adf_version:
            dag_container = dag_container.from_(f"alanmosely/esp-adf:{adf_version}")
        else:
            dag_container = dag_container.from_(f"espressif/idf:{idf_version}")

        return await (
            dag_container.with_mounted_directory("/project", project_dir)
            .with_workdir("/project")
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
                "The version of the Espressif ADF Docker image to use, if specified, idf_version is ignored"
            ),
        ],
        idf_version: Annotated[
            str, Doc("The version of the Espressif IDF Docker image to use")
        ] = DEFAULT_IMAGE_VERSION,
        idf_args: Annotated[list[str], Doc("The arguments to pass to idf.py")] = [
            "build"
        ],
    ) -> str:
        """Execute idf.py from the Espressif IDF or ADF Docker image, by default building the project"""
        return await self._execute_idf_command(
            project_dir, adf_version, idf_version, idf_args
        )

    @function
    async def config(
        self,
        project_dir: Annotated[
            dagger.Directory, Doc("The directory containing the ESP-IDF project")
        ],
        adf_version: Annotated[
            str | None,
            Doc(
                "The version of the Espressif ADF Docker image to use, if specified, idf_version is ignored"
            ),
        ],
        idf_version: Annotated[
            str, Doc("The version of the Espressif IDF Docker image to use")
        ] = DEFAULT_IMAGE_VERSION,
    ) -> str:
        """Execute "idf.py menuconfig" from the official Espressif IDF or ADF Docker image"""
        return await self._execute_idf_command(
            project_dir, adf_version, idf_version, ["fullclean", "menuconfig"]
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
                "The version of the Espressif ADF Docker image to use, if specified, idf_version is ignored"
            ),
        ],
        idf_version: Annotated[
            str, Doc("The version of the Espressif IDF Docker image to use")
        ] = DEFAULT_IMAGE_VERSION,
    ) -> str:
        """Execute "idf.py flash" from the official Espressif IDF or ADF Docker image using the rfc2217 protocol to connect to the host machine's serial port"""
        print(
            "\nRequires esp_rfc2217_server to be running, to set this up, download and run: https://raw.githubusercontent.com/alanmosely/daggerverse/refs/heads/master/esp-idf/src/main/resources/run_esp_rfc2217_server.py"
        )
        print(
            "\nThis will start a server on port 4000 that will forward serial port data to the container, see: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/tools/idf-docker-image.html#using-remote-serial-port\n"
        )
        return await self._execute_idf_command(
            project_dir,
            adf_version,
            idf_version,
            [
                "--port",
                "rfc2217://host.docker.internal:4000?ign_set_control",
                "fullclean",
                "build",
                "flash",
            ],
        )
