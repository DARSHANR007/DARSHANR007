
#!/usr/bin/env python3

"""Update the GitHub profile README with recent public pull requests."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

USERNAME = os.getenv("GITHUB_USERNAME", "DARSHANR007")
README_PATH = Path("README.md")
MAX_PRS = int(os.getenv("MAX_PRS", "12"))

START = "<!-- PR-SHOWCASE:START -->"
END = "<!-- PR-SHOWCASE:END -->"


def fetch_pull_requests():
    """Fetch the latest public pull requests authored by the user."""
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
            "User-Agent": "github-profile-pr-showcase",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(
            f"GitHub API returned HTTP {exc.code}: "
            f"{exc.read().decode('utf-8', errors='replace')}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach GitHub API: {exc}") from exc

    return data.get("items", [])[:MAX_PRS]


def escape_markdown(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def make_badge(label, message, color):
    """Create a compact, colored Shields.io badge."""
    label = quote(label, safe="")
    message = quote(message, safe="")

    return (
        f"![{label} {message}]"
        f"(https://img.shields.io/badge/{label}-{message}-{color}"
        "?style=flat-square&labelColor=161b22)"
    )



def build_showcase(prs):
    """Render a clean, minimal contribution feed without dates."""
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

    summary = " &nbsp; ".join([
        make_badge("+", f"{open_count} Open", "2da44e"),
        make_badge("⑂", f"{merged_count} Merged", "8957e5"),
        make_badge("−", f"{closed_count} Closed", "cf222e"),
    ])

    lines = [
        "<div align=\"center\">",
        "",
        summary,
        "",
        "</div>",
        "",
    ]

    for pr in prs:
        repository = pr.get("repository_url", "").removeprefix(
            "https://api.github.com/repos/"
        )
        url = pr.get("html_url", "")
        title = escape_markdown(pr.get("title", "Untitled PR"))

        if not repository or not url:
            continue

        status_text, color = get_status(pr)
        symbol, label = status_text.split(" ", 1)
        status_badge = make_badge(symbol, label, color)

        pr_number = pr.get("number", "")

        lines.extend([
            f"{status_badge} &nbsp; [**{title}**]({url})",
            "",
            (
                f"<sub>`{escape_markdown(repository)}`"
                f" · PR #{pr_number}</sub>"
            ),
            "",
        ])

    lines.extend([
        "<div align=\"center\">",
        "<sub>Recent public contributions · Automatically updated</sub>",
        "</div>",
    ])

    return "\n".join(lines)



def update_readme(showcase):
    """Replace only the content between the README markers."""
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
        raise ValueError("The README showcase markers are reversed.")

    updated = content[:start] + "\n" + showcase + "\n" + content[end:]

    if updated != content:
        README_PATH.write_text(updated, encoding="utf-8")
        print("README showcase updated.")
    else:
        print("README showcase is already up to date.")


def main():
    print(f"Fetching public PRs for {USERNAME}...")
    prs = fetch_pull_requests()
    print(f"Found {len(prs)} PRs to display.")
    update_readme(build_showcase(prs))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
