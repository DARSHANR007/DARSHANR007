
#!/usr/bin/env python3

"""Update the GitHub profile README with recent public pull requests."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


USERNAME = os.getenv("GITHUB_USERNAME", "DARSHANR007")
README_PATH = Path("README.md")
MAX_PRS = int(os.getenv("MAX_PRS", "12"))

START = "<!-- PR-SHOWCASE:START -->"
END = "<!-- PR-SHOWCASE:END -->"


def fetch_pull_requests():
    """Fetch the newest public PRs authored by the configured user."""
    params = urlencode({
        "q": f"is:pr author:{USERNAME}",
        "sort": "created",
        "order": "desc",
        "per_page": 100,
    })

    request = Request(
        f"https://api.github.com/search/issues?{params}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "profile-pr-showcase",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub API returned HTTP {exc.code}: {details}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Could not reach GitHub API: {exc}"
        ) from exc

    return payload.get("items", [])[:MAX_PRS]


def format_date(value):
    """Format an ISO timestamp as YYYY-MM-DD."""
    if not value:
        return "—"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        return "—"


def escape_markdown(value):
    """Prevent PR titles from breaking Markdown table cells."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def get_status(pr):
    """Return a minimal symbol and status label."""
    details = pr.get("pull_request") or {}

    if details.get("merged_at"):
        return "⑂ Merged"

    if pr.get("state") == "open":
        return "＋ Open"

    return "− Closed"


def build_showcase(prs):
    """Build the compact PR showcase displayed in the README."""
    if not prs:
        return "_No public pull requests found yet._"

    open_count = sum(
        1 for pr in prs if pr.get("state") == "open"
    )
    merged_count = sum(
        1 for pr in prs
        if (pr.get("pull_request") or {}).get("merged_at")
    )
    closed_count = len(prs) - open_count - merged_count

    lines = [
        (
            f"**＋ {open_count} Open**　"
            f"**⑂ {merged_count} Merged**　"
            f"**− {closed_count} Closed**"
        ),
        "",
        "<sub>Recent public pull requests · Automatically updated</sub>",
        "",
        "| Status | Pull request | Repository | Created |",
        "|:--|:--|:--|--:|",
    ]

    for pr in prs:
        repository_url = pr.get("repository_url", "")
        repository = repository_url.removeprefix(
            "https://api.github.com/repos/"
        )
        title = escape_markdown(pr.get("title", "Untitled PR"))
        url = pr.get("html_url", "")
        number = pr.get("number", "")
        created = format_date(pr.get("created_at"))

        if not repository or not url:
            continue

        lines.append(
            f"| {get_status(pr)} "
            f"| [**{title}**]({url}) "
            f"| [`{escape_markdown(repository)}`]"
            f"(https://github.com/{repository}) "
            f"| {created} |"
        )

    lines.extend([
        "",
        "<sub>Showing your latest public pull requests · "
        "Refreshed automatically every six hours</sub>",
    ])

    return "\n".join(lines)


def update_readme(showcase):
    """Replace only the content between the README markers."""
    if not README_PATH.exists():
        raise FileNotFoundError("README.md was not found.")

    content = README_PATH.read_text(encoding="utf-8")

    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError(
            "README.md must contain exactly one "
            "PR-SHOWCASE:START and one PR-SHOWCASE:END marker."
        )

    start = content.index(START) + len(START)
    end = content.index(END)

    if start > end:
        raise ValueError(
            "The README showcase markers are in the wrong order."
        )

    updated = (
        content[:start]
        + "\n"
        + showcase
        + "\n"
        + content[end:]
    )

    if updated != content:
        README_PATH.write_text(updated, encoding="utf-8")
        print("README showcase updated.")
    else:
        print("README showcase is already up to date.")


def main():
    print(f"Fetching public PRs authored by {USERNAME}...")
    prs = fetch_pull_requests()
    print(f"Found {len(prs)} PRs to showcase.")

    update_readme(build_showcase(prs))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
