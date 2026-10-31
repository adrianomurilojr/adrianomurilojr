from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


README_PATH = Path(__file__).resolve().parents[1] / "README.md"
START_MARKER = "<!-- START_SECTION:languages -->"
END_MARKER = "<!-- END_SECTION:languages -->"
API_BASE = "https://api.github.com"


def fetch_json(url: str, token: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-readme-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub API request failed ({error.code}): {details}"
        ) from error


def fetch_repositories(owner: str, token: str) -> list[dict[str, Any]]:
    repositories: list[dict[str, Any]] = []
    page = 1

    while True:
        query = urllib.parse.urlencode(
            {"type": "owner", "per_page": 100, "page": page, "sort": "updated"}
        )
        result = fetch_json(f"{API_BASE}/users/{owner}/repos?{query}", token)
        if not isinstance(result, list):
            raise RuntimeError("GitHub API returned an unexpected repository list.")

        repositories.extend(
            repository
            for repository in result
            if isinstance(repository, dict) and not repository.get("fork", False)
        )
        if len(result) < 100:
            return repositories
        page += 1


def collect_language_bytes(
    repositories: list[dict[str, Any]], owner: str, token: str
) -> dict[str, int]:
    totals: dict[str, int] = {}

    for repository in repositories:
        name = repository.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise RuntimeError("GitHub API returned a repository with an invalid name.")

        languages = fetch_json(
            f"{API_BASE}/repos/{owner}/{name}/languages", token
        )
        if not isinstance(languages, dict):
            raise RuntimeError(f"GitHub API returned invalid languages for {name}.")

        for language, byte_count in languages.items():
            if not isinstance(language, str) or not isinstance(byte_count, int):
                raise RuntimeError(
                    f"GitHub API returned invalid language data for {name}."
                )
            totals[language] = totals.get(language, 0) + byte_count

    return totals


def render_language_badges(language_bytes: dict[str, int]) -> str:
    total_bytes = sum(language_bytes.values())
    if total_bytes == 0:
        raise RuntimeError("No languages were found in the public repositories.")

    badges = []
    for language, byte_count in sorted(
        language_bytes.items(), key=lambda item: (-item[1], item[0].casefold())
    ):
        percentage = byte_count / total_bytes * 100
        label = urllib.parse.quote(language, safe="")
        badges.append(
            f'![{language}](https://img.shields.io/badge/{label}-'
            f'{percentage:.1f}%25-3178C6?style=for-the-badge)'
        )

    return "\n".join(badges)


def update_readme(badges: str, repository_count: int) -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    if readme.count(START_MARKER) != 1 or readme.count(END_MARKER) != 1:
        raise RuntimeError("README language section markers are missing or duplicated.")

    start = readme.index(START_MARKER) + len(START_MARKER)
    end = readme.index(END_MARKER)
    if start >= end:
        raise RuntimeError("README language section markers are out of order.")

    generated = (
        "\n\n"
        f"{badges}\n"
        "\n"
        f"<sub>Automatically generated from {repository_count} public, "
        "non-fork repositories.</sub>\n"
    )
    updated = readme[:start] + generated + readme[end:]
    if updated != readme:
        README_PATH.write_text(updated, encoding="utf-8", newline="\n")


def main() -> None:
    owner = os.environ.get("PROFILE_OWNER", "adrianomurilojr")
    if not re.fullmatch(r"[A-Za-z0-9-]+", owner):
        raise RuntimeError("PROFILE_OWNER contains invalid characters.")

    token = os.environ.get("GITHUB_TOKEN", "")
    repositories = fetch_repositories(owner, token)
    if not repositories:
        raise RuntimeError(f"No public repositories were found for {owner}.")

    language_bytes = collect_language_bytes(repositories, owner, token)
    badges = render_language_badges(language_bytes)
    update_readme(badges, len(repositories))
    print(f"Updated language badges from {len(repositories)} public repositories.")


if __name__ == "__main__":
    main()
