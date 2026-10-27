
def build_showcase(prs):
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
            f"![Open](https://img.shields.io/badge/Open-{open_count}"
            "-2da44e?style=flat-square)"
            f" ![Merged](https://img.shields.io/badge/Merged-{merged_count}"
            "-8957e5?style=flat-square)"
            f" ![Closed](https://img.shields.io/badge/Closed-{closed_count}"
            "-cf222e?style=flat-square)"
        ),
        "",
        "| Status | Pull request | Repository |",
        "|:--|:--|:--|",
    ]

    for pr in prs:
        details = pr.get("pull_request") or {}

        if details.get("merged_at"):
            status = (
                "[![Merged](https://img.shields.io/badge/⑂-Merged-"
                "8957e5?style=flat-square)]"
            )
        elif pr.get("state") == "open":
            status = (
                "[![Open](https://img.shields.io/badge/＋-Open-"
                "2da44e?style=flat-square)]"
            )
        else:
            status = (
                "[![Closed](https://img.shields.io/badge/−-Closed-"
                "cf222e?style=flat-square)]"
            )

        repository = pr.get("repository_url", "").removeprefix(
            "https://api.github.com/repos/"
        )
        title = escape_markdown(pr.get("title", "Untitled PR"))
        url = pr.get("html_url", "")

        if not repository or not url:
            continue

        lines.append(
            f"| {status} "
            f"| [**{title}**]({url}) "
            f"| [`{escape_markdown(repository)}`]"
            f"(https://github.com/{repository}) |"
        )

    lines.extend([
        "",
        "<sub>Latest public pull requests · Automatically updated</sub>",
    ])

    return "\n".join(lines)
