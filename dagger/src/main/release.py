import json
import re
from datetime import datetime, timezone
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type

DEFAULT_REPO = "alanmosely/daggerverse"
GITHUB_API_VERSION = "2022-11-28"
CURL_IMAGE = "curlimages/curl:8.21.0"


@object_type
class Daggerverse:
    async def _create_release(
        self,
        token: dagger.Secret,
        tag: str,
        name: str | None,
        repo: str,
        target: str | None,
        generate_notes: bool,
        body: str | None,
        draft: bool,
        prerelease: bool,
    ) -> str:
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            raise ValueError(f"Invalid repo (expected owner/name): {repo}")

        release_name = name or tag
        payload: dict[str, object] = {
            "tag_name": tag,
            "name": release_name,
            "draft": draft,
            "prerelease": prerelease,
        }

        if target:
            payload["target_commitish"] = target

        if generate_notes:
            payload["generate_release_notes"] = True
        else:
            payload["body"] = body or ""

        payload_json = json.dumps(payload)

        return await (
            dag.container()
            .from_(CURL_IMAGE)
            .with_secret_variable("GITHUB_TOKEN", token)
            .with_new_file("/payload.json", payload_json)
            # creating a release is a side effect; never serve it from cache
            .with_env_variable(
                "CACHE_BUSTER", datetime.now(timezone.utc).isoformat()
            )
            .with_exec(
                [
                    "curl",
                    "--fail-with-body",
                    "-sS",
                    "-X",
                    "POST",
                    "-H",
                    "Accept: application/vnd.github+json",
                    "-H",
                    f"X-GitHub-Api-Version: {GITHUB_API_VERSION}",
                    "--variable",
                    "%GITHUB_TOKEN",
                    "--expand-header",
                    "Authorization: Bearer {{GITHUB_TOKEN}}",
                    "--data-binary",
                    "@/payload.json",
                    f"https://api.github.com/repos/{repo}/releases",
                ]
            )
            .stdout()
        )

    @function
    async def release(
        self,
        token: Annotated[dagger.Secret, Doc("GitHub token with repo scope")],
        tag: Annotated[str, Doc("Release tag name, e.g. esp-idf/v0.0.4")],
        name: Annotated[str | None, Doc("Release name (defaults to tag)")] = None,
        repo: Annotated[str, Doc("GitHub repo (owner/name)")] = DEFAULT_REPO,
        target: Annotated[
            str | None, Doc("Commitish to tag (branch, SHA, etc.)")
        ] = None,
        generate_notes: Annotated[
            bool, Doc("Use GitHub auto-generated release notes")
        ] = True,
        body: Annotated[
            str | None, Doc("Release body (ignored if generate_notes is true)")
        ] = None,
        draft: Annotated[bool, Doc("Create release as draft")] = False,
        prerelease: Annotated[bool, Doc("Mark release as pre-release")] = False,
    ) -> str:
        """Create a GitHub release for the given tag."""
        return await self._create_release(
            token, tag, name, repo, target, generate_notes, body, draft, prerelease
        )

    @function
    async def release_module(
        self,
        token: Annotated[dagger.Secret, Doc("GitHub token with repo scope")],
        module: Annotated[str, Doc("Module name, e.g. esp-idf")],
        version: Annotated[str, Doc("Version tag, e.g. v0.0.4")],
        repo: Annotated[str, Doc("GitHub repo (owner/name)")] = DEFAULT_REPO,
        target: Annotated[
            str | None, Doc("Commitish to tag (branch, SHA, etc.)")
        ] = None,
        generate_notes: Annotated[
            bool, Doc("Use GitHub auto-generated release notes")
        ] = True,
        body: Annotated[
            str | None, Doc("Release body (ignored if generate_notes is true)")
        ] = None,
        draft: Annotated[bool, Doc("Create release as draft")] = False,
        prerelease: Annotated[bool, Doc("Mark release as pre-release")] = False,
    ) -> str:
        """Create a GitHub release for module/version tags (module/version)."""
        tag = f"{module}/{version}"
        name = f"{module} {version}"
        return await self._create_release(
            token, tag, name, repo, target, generate_notes, body, draft, prerelease
        )
