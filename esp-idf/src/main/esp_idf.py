from typing import Annotated

import dagger
from dagger import dag, Doc, function, object_type


@object_type
class EspIdf:
    @function
    async def run(
        self,
        project_dir: Annotated[
            dagger.Directory, Doc("The directory containing the ESP-IDF project")
        ],
        image_version: Annotated[
            str, Doc("The version of the Espressif IDF Docker image to use")
        ] = "v5.1",
        idf_args: Annotated[list[str], Doc("The arguments to pass to idf.py")] = [
            "build"
        ],
    ) -> str:
        """Execute idf.py from the official Espressif IDF Docker image

        Example usage: dagger call run --project_dir . --image_version "v5.2"
        """
        run_output = await (
            dag.container()
            .from_(f"espressif/idf:{image_version}")
            .with_mounted_directory("/project", project_dir)
            .with_workdir("/project")
            .with_exec(["idf.py", *idf_args], use_entrypoint=True)
            .stdout()
        )
        return run_output
