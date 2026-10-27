
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

    def badge(label, color):
        return (
            f"![{label}](https://img.shields.io/badge/"
            f"{label}-{color}?style=flat-square&labelColor=0d1117)"
        )

    lines = [
        (
            f"{badge(f'+ {open_count} Open', '2da44e')} "
            f"{badge(f'⑂ {merged_count} Merged', '8957e5')} "
            f"{badge(f'− {closed_count} Closed', 'cf222e')}"
        ),
        "",
        "| Status | Pull request | Repository |",
        "|:--|:--|:--|",
    ]

    for pr in prs:
        details = pr.get("pull_request") or {}

        if details.get("merged_at"):
            status = badge("⑂ Merged", "8957e5")
        elif pr.get("state") == "open":
            status = badge("+ Open", "2da44e")
        else:
            status = badge("− Closed", "cf222e")

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
