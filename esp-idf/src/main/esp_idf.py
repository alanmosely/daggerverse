import dagger
from dagger import dag, function, object_type


@object_type
class EspIdf:
    @function
    async def build(
        self,
        project_dir: dagger.Directory,
        image_version: str = "v5.1",
        idf_args: list = ["build"],
    ) -> str:
        """Executes idf.py from the ESP-IDF Docker image"""

        build_output = await (
            dag.container()
            .from_(f"espressif/idf:{image_version}")
            .with_mounted_directory("/project", project_dir)
            .with_workdir("/project")
            .with_exec(["idf.py", *idf_args], use_entrypoint=True)
            .stdout()
        )
        return build_output
