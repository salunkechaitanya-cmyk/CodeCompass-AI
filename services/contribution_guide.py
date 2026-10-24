
"""Find beginner-friendly GitHub issues."""

import requests

GITHUB_API = "https://api.github.com"

BEGINNER_LABELS = {
    "good first issue",
    "good-first-issue",
    "beginner",
    "beginner-friendly",
    "help wanted",
    "up-for-grabs",
    "first-timers-only",
}


def get_beginner_issues(owner, repo, limit=10):
    """Find beginner-friendly issues in the selected repository."""

    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"

    try:
        response = requests.get(
            url,
            params={
                "state": "open",
                "per_page": 100,
                "sort": "created",
                "direction": "desc",
            },
            headers={"Accept": "application/vnd.github+json"},
            timeout=15,
        )

        if response.status_code == 404:
            return [], "Repository not found or issues are unavailable."

        if response.status_code == 403:
            return [], "GitHub API rate limit reached. Please try later."

        response.raise_for_status()
        issues = response.json()

        if not isinstance(issues, list):
            return [], "GitHub returned an unexpected response."

        matches = []

        for issue in issues:
            if "pull_request" in issue:
                continue

            labels = {
                label.get("name", "").strip().lower()
                for label in issue.get("labels", [])
                if isinstance(label, dict)
            }

            matched_labels = labels.intersection(BEGINNER_LABELS)

            if matched_labels:
                issue["beginner_labels"] = sorted(matched_labels)
                matches.append(issue)

            if len(matches) >= limit:
                break

        return matches, None

    except requests.exceptions.Timeout:
        return [], "GitHub took too long to respond. Please try again."
    except requests.exceptions.RequestException:
        return [], "Could not retrieve issues from GitHub. Check your connection."
    except (ValueError, TypeError, AttributeError):
        return [], "GitHub returned an unexpected response."


def search_global_beginner_issues(limit=10):
    """Search public GitHub repositories for beginner-friendly issues."""

    query = (
        'is:issue is:open '
        'label:"good first issue"'
    )

    try:
        response = requests.get(
            f"{GITHUB_API}/search/issues",
            params={
                "q": query,
                "sort": "created",
                "order": "desc",
                "per_page": min(max(limit, 1), 30),
            },
            headers={"Accept": "application/vnd.github+json"},
            timeout=15,
        )

        if response.status_code == 403:
            return [], "GitHub search rate limit reached. Please try later."

        response.raise_for_status()
        result = response.json()
        issues = result.get("items", [])

        for issue in issues:
            issue["beginner_labels"] = [
                label.get("name", "")
                for label in issue.get("labels", [])
                if isinstance(label, dict)
            ]

        return issues, None

    except requests.exceptions.Timeout:
        return [], "GitHub took too long to respond. Please try again."
    except requests.exceptions.RequestException:
        return [], "Could not search GitHub. Please try again later."
    except (ValueError, TypeError, AttributeError):
        return [], "GitHub returned an unexpected response."


def make_contribution_steps(issue):
    """Create a beginner-friendly contribution checklist."""

    title = issue.get("title", "Untitled issue")
    body = issue.get("body") or "No detailed description was provided."
    issue_url = issue.get("html_url", "")
    labels = issue.get("beginner_labels", [])

    return f"""
### 1. Understand the issue

**Issue:** {title}

**Labels:** {", ".join(labels) or "Not specified"}

{body[:2500]}

[Open this issue on GitHub]({issue_url})

### 2. Check before coding

- Read the repository README.
- Check for CONTRIBUTING.md.
- Look for related code and tests.
- Check whether someone is already working on the issue.
- Ask a maintainer for clarification if needed.

### 3. Prepare your workspace

1. Fork the repository on GitHub.
2. Clone your fork to your computer.
3. Create a separate branch for your change.
4. Install the documented dependencies.

### 4. Make a small change

- Follow the issue requirements.
- Match the project's coding style.
- Add or update tests when appropriate.
- Run relevant tests.

### 5. Submit your contribution

1. Review your changes.
2. Commit with a clear message.
3. Push your branch to your fork.
4. Open a pull request against the original repository.
5. Explain your changes and link the issue.
6. Respond to review feedback.
"""
