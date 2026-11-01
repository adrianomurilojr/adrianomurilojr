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
TECH_START_MARKER = "<!-- START_SECTION:technologies -->"
TECH_END_MARKER = "<!-- END_SECTION:technologies -->"
API_BASE = "https://api.github.com"

LANGUAGE_BADGES = {
    "C": ("555555", "c", "white"),
    "C#": ("512BD4", None, "white"),
    "C++": ("00599C", "cplusplus", "white"),
    "CSS": ("1572B6", "css", "white"),
    "Dart": ("0175C2", "dart", "white"),
    "Go": ("00ADD8", "go", "white"),
    "HTML": ("E34F26", "html5", "white"),
    "Java": ("007396", "openjdk", "white"),
    "JavaScript": ("F7DF1E", "javascript", "black"),
    "Kotlin": ("7F52FF", "kotlin", "white"),
    "PHP": ("777BB4", "php", "white"),
    "Python": ("3776AB", "python", "white"),
    "Ruby": ("CC342D", "ruby", "white"),
    "Rust": ("000000", "rust", "white"),
    "Shell": ("4EAA25", "gnubash", "white"),
    "Swift": ("F05138", "swift", "white"),
    "TypeScript": ("3178C6", "typescript", "white"),
}

TECHNOLOGIES = {
    "@angular/core": ("Frontend", "Angular", "angular", "0F0F11"),
    "@remix-run/react": ("Frontend", "Remix", "remix", "000000"),
    "@vitejs/plugin-react": ("Frontend", "Vite", "vite", "646CFF"),
    "autoprefixer": (
        "Libraries & tooling",
        "Autoprefixer",
        "autoprefixer",
        "DD3735",
    ),
    "astro": ("Frontend", "Astro", "astro", "BC52EE"),
    "next": ("Frontend", "Next.js", "nextdotjs", "000000"),
    "nuxt": ("Frontend", "Nuxt", "nuxt", "00DC82"),
    "react": ("Frontend", "React", "react", "149ECA"),
    "solid-js": ("Frontend", "Solid", "solid", "2C4F7C"),
    "svelte": ("Frontend", "Svelte", "svelte", "FF3E00"),
    "tailwindcss": ("Frontend", "Tailwind CSS", "tailwindcss", "06B6D4"),
    "vite": ("Frontend", "Vite", "vite", "646CFF"),
    "vue": ("Frontend", "Vue.js", "vuedotjs", "4FC08D"),
    "@fastify/cors": ("Backend & data", "Fastify", "fastify", "000000"),
    "@fastify/jwt": ("Backend & data", "Fastify", "fastify", "000000"),
    "@fastify/type-provider-zod": ("Backend & data", "Fastify", "fastify", "000000"),
    "@prisma/client": ("Backend & data", "Prisma", "prisma", "2D3748"),
    "drizzle-orm": ("Backend & data", "Drizzle", "drizzle", "C5F74F"),
    "express": ("Backend & data", "Express", "express", "000000"),
    "fastify": ("Backend & data", "Fastify", "fastify", "000000"),
    "fastify-type-provider-zod": (
        "Backend & data",
        "Fastify",
        "fastify",
        "000000",
    ),
    "mongodb": ("Backend & data", "MongoDB", "mongodb", "47A248"),
    "mongoose": ("Backend & data", "Mongoose", "mongoose", "880000"),
    "mysql2": ("Backend & data", "MySQL", "mysql", "4479A1"),
    "pg": ("Backend & data", "PostgreSQL", "postgresql", "4169E1"),
    "postgres": ("Backend & data", "PostgreSQL", "postgresql", "4169E1"),
    "prisma": ("Backend & data", "Prisma", "prisma", "2D3748"),
    "sequelize": ("Backend & data", "Sequelize", "sequelize", "52B0E7"),
    "zod": ("Backend & data", "Zod", "zod", "3E67B1"),
    "bcrypt": ("Libraries & tooling", "bcrypt", None, "003A70"),
    "bcryptjs": ("Libraries & tooling", "bcryptjs", None, "003A70"),
    "cors": ("Libraries & tooling", "CORS", None, "555555"),
    "dotenv": ("Libraries & tooling", "dotenv", "dotenv", "ECD53F"),
    "eslint": ("Libraries & tooling", "ESLint", "eslint", "4B32C3"),
    "framer-motion": ("Libraries & tooling", "Motion", "framer", "0055FF"),
    "helmet": ("Libraries & tooling", "Helmet", None, "000000"),
    "jsonwebtoken": ("Libraries & tooling", "JWT", "jsonwebtokens", "000000"),
    "lucide": ("Libraries & tooling", "Lucide", "lucide", "F56565"),
    "lucide-react": ("Libraries & tooling", "Lucide", "lucide", "F56565"),
    "motion": ("Libraries & tooling", "Motion", "framer", "0055FF"),
    "morgan": ("Libraries & tooling", "Morgan", None, "555555"),
    "multer": ("Libraries & tooling", "Multer", None, "555555"),
    "pdfkit": ("Libraries & tooling", "PDFKit", None, "B40B0B"),
    "postcss": ("Libraries & tooling", "PostCSS", "postcss", "DD3A0A"),
    "recharts": ("Libraries & tooling", "Recharts", None, "22B5BF"),
    "tsx": ("Libraries & tooling", "tsx", None, "3178C6"),
    "typescript": ("Libraries & tooling", "TypeScript", "typescript", "3178C6"),
    "vitest": ("Libraries & tooling", "Vitest", "vitest", "6E9F18"),
}


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


def fetch_package_json(
    owner: str, repository: dict[str, Any]
) -> dict[str, Any] | None:
    name = repository.get("name")
    branch = repository.get("default_branch")
    if not isinstance(name, str) or not isinstance(branch, str):
        raise RuntimeError(
            "GitHub API returned a repository without a valid name or branch."
        )

    url = (
        f"https://raw.githubusercontent.com/{owner}/{name}/"
        f"{urllib.parse.quote(branch, safe='/')}/package.json"
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "github-profile-readme-updater"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Could not read package.json for {name} ({error.code}): {details}"
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid package.json in repository {name}.") from error

    if not isinstance(result, dict):
        raise RuntimeError(f"GitHub returned an invalid package.json for {name}.")
    return result


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
            if isinstance(repository, dict)
            and not repository.get("fork", False)
            and not repository.get("private", False)
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


def collect_technologies(
    repositories: list[dict[str, Any]], owner: str
) -> dict[str, tuple[str, str, str | None, str]]:
    detected: dict[str, tuple[str, str, str | None, str]] = {}
    for repository in repositories:
        package = fetch_package_json(owner, repository)
        if package is None:
            continue

        detected["Node.js"] = (
            "Backend & data",
            "Node.js",
            "nodedotjs",
            "339933",
        )
        for section in (
            "dependencies",
            "devDependencies",
            "peerDependencies",
            "optionalDependencies",
        ):
            dependencies = package.get(section, {})
            if not isinstance(dependencies, dict):
                raise RuntimeError(
                    f"GitHub returned an invalid {section} in "
                    f"{repository.get('name')}/package.json."
                )
            for name in dependencies:
                if not isinstance(name, str):
                    continue
                technology = TECHNOLOGIES.get(name.casefold())
                if technology:
                    detected[technology[1]] = technology
                elif not name.startswith("@types/"):
                    detected[name] = (
                        "Other dependencies",
                        name,
                        None,
                        "64748B",
                    )

    return detected


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
        color, logo, logo_color = LANGUAGE_BADGES.get(
            language, ("3178C6", None, "white")
        )
        query = {"style": "for-the-badge"}
        if logo:
            query.update({"logo": logo, "logoColor": logo_color})
        badges.append(
            f'![{language}](https://img.shields.io/badge/{label}-'
            f'{percentage:.1f}%25-{color}?{urllib.parse.urlencode(query)})'
        )

    return "\n".join(badges)


def render_technology_badges(
    technologies: dict[str, tuple[str, str, str | None, str]]
) -> str:
    categories: dict[str, list[str]] = {}
    for category, name, logo, color in sorted(
        technologies.values(), key=lambda item: (item[0], item[1].casefold())
    ):
        query = {"style": "flat-square"}
        if logo:
            query.update({"logo": logo, "logoColor": "white"})
        badge = (
            f"![{name}](https://img.shields.io/badge/"
            f"{urllib.parse.quote(name, safe='')}-{color}?"
            f"{urllib.parse.urlencode(query)})"
        )
        categories.setdefault(category, []).append(badge)

    return "\n\n".join(
        f"### {category}\n\n" + " ".join(badges)
        for category, badges in categories.items()
    )


def replace_section(
    readme: str, start_marker: str, end_marker: str, content: str
) -> str:
    if readme.count(start_marker) != 1 or readme.count(end_marker) != 1:
        raise RuntimeError(
            f"README section markers are missing or duplicated: {start_marker}."
        )

    start = readme.index(start_marker) + len(start_marker)
    end = readme.index(end_marker)
    if start >= end:
        raise RuntimeError(f"README section markers are out of order: {start_marker}.")

    return readme[:start] + "\n\n" + content + "\n" + readme[end:]


def update_readme(
    language_badges: str,
    technology_badges: str,
    repository_count: int,
) -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    language_content = (
        f"{language_badges}\n\n"
        f"<sub>Automatically generated from {repository_count} public, "
        "non-fork repositories.</sub>"
    )
    updated = replace_section(
        readme, START_MARKER, END_MARKER, language_content
    )
    updated = replace_section(
        updated, TECH_START_MARKER, TECH_END_MARKER, technology_badges
    )
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
    technologies = collect_technologies(repositories, owner)
    update_readme(
        render_language_badges(language_bytes),
        render_technology_badges(technologies),
        len(repositories),
    )
    print(
        f"Updated languages and {len(technologies)} technologies "
        f"from {len(repositories)} public repositories."
    )


if __name__ == "__main__":
    main()
