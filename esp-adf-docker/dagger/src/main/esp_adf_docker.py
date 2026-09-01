import re
from typing import Annotated

import dagger
from dagger import Container, Doc, function, object_type


@object_type
class EspAdfDocker:
    """The ESP-ADF (Espressif Audio Development Framework) is the official audio development framework for the ESP32 chip series by Espressif"""

    registry: Annotated[str, Doc("Registry to publish to")] = "docker.io"
    username: Annotated[
        str, Doc("Registry username/namespace to publish under")
    ] = "alanmosely"

    @function
    def build(
        self,
        src: Annotated[
            dagger.Directory,
            Doc("Location of directory containing Dockerfile"),
        ],
    ) -> Container:
        """Build image from Dockerfile"""
        return src.docker_build()

    @function
    async def publish(
        self,
        src: Annotated[
            dagger.Directory, Doc("Location of directory containing Dockerfile")
        ],
        token: Annotated[dagger.Secret, Doc("Docker PAT")],
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

        return (
            await self.build(src)
            .with_registry_auth(self.registry, self.username, token)
            .publish(
                f"{self.registry}/{self.username}/esp-adf:"
                f"adf-{adf_release}-idf-{idf_release}"
            )
        )
