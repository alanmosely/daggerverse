import re
from typing import Annotated

import dagger
from dagger import Container, Doc, dag, function, object_type


@object_type
class EspAdfDocker:
    """The ESP-ADF (Espressif Audio Development Framework) is the official audio development framework for the ESP32 chip series by Espressif"""

    def get_workspace(self, src: dagger.Directory) -> dagger.Directory:
        """Helper method to create the workspace"""
        return (
            dag.container()
            .with_directory("/src", src)
            .with_workdir("/src")
            .directory("/src")
        )

    @function
    async def build(
        self,
        src: Annotated[
            dagger.Directory,
            Doc("Location of directory containing Dockerfile"),
        ],
    ) -> Container:
        """Build image from Dockerfile"""
        workspace = self.get_workspace(src)

        return await dag.container().build(
            context=workspace, build_args=[dagger.BuildArg("DOCKER_BUILDKIT", "1")]
        )

    @function
    async def publish(
        self,
        src: Annotated[
            dagger.Directory, Doc("Location of directory containing Dockerfile")
        ],
        token: Annotated[dagger.Secret, Doc("Docker PAT")],
        registry: str = "docker.io",
        username: str = "alanmosely",
    ) -> str:
        """Build image and publish to DockerHub with tag adf-<ADF_RELEASE>-idf-<IDF_RELEASE>"""

        file_content = await src.file("Dockerfile").contents()
        adf_match = re.search(r"ARG\s+ADF_RELEASE\s*=\s*(\S+)", file_content)
        idf_match = re.search(r"ARG\s+IDF_RELEASE\s*=\s*(\S+)", file_content)

        if adf_match:
            adf_release = adf_match.group(1)
        else:
            raise ValueError("ADF_RELEASE not found in Dockerfile")

        if idf_match:
            idf_release = idf_match.group(1)
        else:
            raise ValueError("IDF_RELEASE not found in Dockerfile")

        workspace = self.get_workspace(src)

        return (
            await dag.container()
            .build(
                context=workspace,
                build_args=[dagger.BuildArg("DOCKER_BUILDKIT", "1")],
            )
            .with_registry_auth(registry, username, token)
            .publish(f"{registry}/{username}/esp-adf:adf-{adf_release}-idf-{idf_release}")
        )
