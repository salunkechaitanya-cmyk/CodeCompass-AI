
import base64
import os
from urllib.parse import quote, urlparse

import requests
import streamlit as st

GITHUB_API = "https://api.github.com"

BASE_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def parse_repo_url(repo_url):
    """Extract owner and repository name from a GitHub URL."""
    if not isinstance(repo_url, str) or not repo_url.strip():
        raise ValueError("Enter a GitHub repository URL.")

    repo_url = repo_url.strip()

    if repo_url.startswith("github.com/"):
        repo_url = "https://" + repo_url

    parsed = urlparse(repo_url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Enter a valid HTTPS GitHub repository URL.")

    if parsed.hostname not in ("github.com", "www.github.com"):
        raise ValueError("Please use a URL from github.com.")

    parts = parsed.path.strip("/").split("/")

    if len(parts) != 2 or not all(parts):
        raise ValueError(
            "Use this format: https://github.com/owner/repository"
        )

    owner, repo = parts
    repo = repo.removesuffix(".git")

    if not owner or not repo:
        raise ValueError("Repository owner or name is missing.")

    return owner, repo


def get_headers():
    """Build GitHub API headers."""
    headers = BASE_HEADERS.copy()
    token = os.getenv("GITHUB_TOKEN", "")

    if not token:
        try:
            token = st.secrets.get("GITHUB_TOKEN", "")
        except Exception:
            token = ""

    if token and token != "paste_your_token_here":
        headers["Authorization"] = f"Bearer {token}"

    return headers




def github_get(endpoint, params=None):
    """Send an authenticated request to the GitHub API."""
    import os
    import streamlit as st
    import requests

    url = f"{GITHUB_API}/{endpoint.lstrip('/')}"

    try:
        token = st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        token = ""

    token = token or os.getenv("GITHUB_TOKEN", "")

    headers = get_headers().copy()

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20,
        )

        if response.status_code == 401:
            raise ValueError(
                "GitHub rejected the token. Check that GITHUB_TOKEN "
                "is valid and has not expired."
            )

        if response.status_code == 403:
            remaining = response.headers.get(
                "X-RateLimit-Remaining"
            )
            reset_time = response.headers.get(
                "X-RateLimit-Reset"
            )

            if remaining == "0":
                message = (
                    "GitHub API rate limit reached. "
                    "Check your token and wait for the reset time."
                )

                if reset_time:
                    message += (
                        f" Reset timestamp: {reset_time}."
                    )

                raise ValueError(message)

            raise ValueError(
                "GitHub denied the request. Check token permissions "
                "or GitHub's abuse-rate-limit response."
            )

        if response.status_code == 404:
            raise ValueError(
                "Repository or resource not found. Check the URL "
                "and ensure the repository is public."
            )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout as error:
        raise ValueError(
            "GitHub took too long to respond. Try again."
        ) from error

    except requests.exceptions.ConnectionError as error:
        raise ValueError(
            "Could not connect to GitHub. Check your internet."
        ) from error

    except requests.exceptions.HTTPError as error:
        raise ValueError(
            f"GitHub HTTP error: {error}"
        ) from error


def get_repo_data(repo_url):
    """Return the repository's main details."""
    owner, repo = parse_repo_url(repo_url)
    return github_get(f"repos/{owner}/{repo}")


def get_languages(owner, repo):
    """Return language byte counts."""
    return github_get(f"repos/{owner}/{repo}/languages")


def get_file_tree(owner, repo, branch="main"):
    """Return files and folders on a branch."""
    encoded_branch = quote(branch, safe="")
    result = github_get(
        f"repos/{owner}/{repo}/git/trees/{encoded_branch}",
        params={"recursive": "1"},
    )
    return result.get("tree", [])


def get_readme(owner, repo):
    """Return decoded README text."""
    try:
        result = github_get(f"repos/{owner}/{repo}/readme")
        content = result.get("content", "")

        if not content:
            return None

        return base64.b64decode(content).decode(
            "utf-8",
            errors="replace",
        )

    except ValueError as error:
        if "not found" in str(error).lower():
            return None
        raise


def get_latest_commit(owner, repo):
    """Return details of the latest commit."""
    commits = github_get(
        f"repos/{owner}/{repo}/commits",
        params={"per_page": 1},
    )

    if not commits:
        return None

    item = commits[0]
    details = item.get("commit", {})
    author_details = details.get("author") or {}

    return {
        "message": details.get("message", "No commit message"),
        "author": (
            author_details.get("name")
            or (item.get("author") or {}).get("login")
            or "Unknown"
        ),
        "date": author_details.get("date", "Unknown"),
        "url": item.get("html_url", ""),
        "sha": item.get("sha", "")[:7],
    }


def get_contributors(owner, repo, limit=10):
    """Return repository contributors."""
    return github_get(
        f"repos/{owner}/{repo}/contributors",
        params={"per_page": limit},
    )


def get_open_issues(owner, repo, limit=20):
    """Return open issues, excluding pull requests."""
    issues = github_get(
        f"repos/{owner}/{repo}/issues",
        params={"state": "open", "per_page": limit},
    )

    return [
        issue for issue in issues
        if "pull_request" not in issue
    ]

def check_github_auth():
    """Safely check whether GitHub authentication is working."""
    import os
    import requests
    import streamlit as st

    try:
        token = st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        token = ""

    token = token or os.getenv("GITHUB_TOKEN", "")

    headers = get_headers().copy()

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(
        "https://api.github.com/rate_limit",
        headers=headers,
        timeout=15,
    )

    try:
        data = response.json()
    except ValueError:
        data = {}

    core = data.get("resources", {}).get("core", {})

    return {
        "token_present": bool(token),
        "http_status": response.status_code,
        "rate_limit": core.get("limit", "Unknown"),
        "remaining": core.get("remaining", "Unknown"),
        "reset_timestamp": core.get("reset", "Unknown"),
    }

def get_file_content(owner, repo, path, branch="main"):
    """Fetch and decode a text file from a public GitHub repository."""
    import base64
    from urllib.parse import quote

    encoded_path = quote(path, safe="/")

    result = github_get(
        f"repos/{owner}/{repo}/contents/{encoded_path}",
        params={"ref": branch},
    )

    if not isinstance(result, dict):
        raise ValueError("GitHub returned an unexpected response.")

    if result.get("type") != "file":
        raise ValueError("The selected path is not a file.")

    content = result.get("content", "")
    encoding = result.get("encoding", "")

    if encoding != "base64" or not content:
        raise ValueError("This file cannot be previewed as ordinary text.")

    try:
        return base64.b64decode(content).decode(
            "utf-8",
            errors="replace",
        )
    except Exception as error:
        raise ValueError("Could not decode this file.") from error


