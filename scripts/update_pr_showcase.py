
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
            "User-Agent": "profile-pr-showcase",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"GitHub API request failed: {exc}") from exc

    return data.get("items", [])[:MAX_PRS]


def format_date(value):
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).strftime("%Y-%m-%d")
    except ValueError:
        return "—"


def escape_markdown(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def build_showcase(prs):
    if not prs:
        return (
            "_No public pull requests found yet. "
            "Your contributions will appear here automatically._"
        )

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
            f"![Open](https://img.shields.io/badge/Open-{open_count}"
            "-2ea44f?style=flat-square)"
            f" ![Merged](https://img.shields.io/badge/Merged-{merged_count}"
            "-8957e5?style=flat-square)"
            f" ![Closed](https://img.shields.io/badge/Closed-{closed_count}"
            "-6e7781?style=flat-square)"
        ),
        "",
        "<sub>Recent public pull requests · Automatically updated</sub>",
        "",
    ]

    for index, pr in enumerate(prs):
        details = pr.get("pull_request") or {}

        if details.get("merged_at"):
            status = "🟣 Merged"
        elif pr.get("state") == "open":
            status = "🟢 Open"
        else:
            status = "⚪ Closed"

        repository = pr.get("repository_url", "").removeprefix(
            "https://api.github.com/repos/"
        )
        title = escape_markdown(pr.get("title", "Untitled PR"))
        url = pr.get("html_url", "")
        created = format_date(pr.get("created_at"))
        number = pr.get("number", "")

        if not repository or not url:
            continue

        # Each PR gets a compact, GitHub-compatible card.
        lines.extend([
            "<table>",
            "<tr>",
            '<td width="28" valign="top">',
            f"<strong>{status}</strong>",
            "</td>",
            "<td>",
            f"<strong><a href=\"{url}\">{title}</a></strong>",
            "<br/>",
            (
                f"<sub><a href=\"https://github.com/{repository}\">"
                f"{escape_markdown(repository)}</a>"
                f" · PR #{number} · Created {created}</sub>"
            ),
            "</td>",
            "</tr>",
            "</table>",
            "",
        ])

    lines.extend([
        "<sub>Showing your latest public pull requests, "
        "refreshed automatically every six hours.</sub>",
    ])

    return "\n".join(lines)



def update_readme(showcase):
    if not README_PATH.exists():
        raise FileNotFoundError("README.md was not found.")

    content = README_PATH.read_text(encoding="utf-8")

    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError(
            "README.md must contain exactly one showcase START "
            "marker and one showcase END marker."
        )

    start = content.index(START) + len(START)
    end = content.index(END)

    if start > end:
        raise ValueError("Showcase markers are in the wrong order.")

    updated = content[:start] + "\n" + showcase + "\n" + content[end:]

    if updated != content:
        README_PATH.write_text(updated, encoding="utf-8")
        print("README showcase updated.")
    else:
        print("README showcase is already up to date.")


def main():
    print(f"Fetching public pull requests for {USERNAME}...")
    prs = fetch_pull_requests()
    print(f"Displaying {len(prs)} pull requests.")
    update_readme(build_showcase(prs))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
