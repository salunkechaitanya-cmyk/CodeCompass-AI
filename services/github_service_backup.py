
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
    repo_url = repo_url.strip()

    if repo_url.startswith("github.com/"):
        repo_url = "https://" + repo_url

    parsed = urlparse(repo_url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Enter a valid GitHub repository URL.")

    if parsed.hostname not in ("github.com", "www.github.com"):
        raise ValueError("Please use a URL from github.com.")

    parts = parsed.path.strip("/").split("/")

    if len(parts) != 2 or not all(parts):
        raise ValueError(
            "Use a URL like https://github.com/owner/repository"
        )

    owner, repo = parts
    repo = repo.removesuffix(".git")

    if not owner or not repo:
        raise ValueError("Repository owner or name is missing.")

    return owner, repo


def get_headers():
    """Build request headers without exposing or requiring a token."""
    headers = BASE_HEADERS.copy()

    token = os.getenv("GITHUB_TOKEN", "")

    if not token:
        try:
            token = st.secrets.get("GITHUB_TOKEN", "")
        except Exception:
            token = ""

    # Ignore the placeholder used in a fresh project setup.
    if token and token != "paste_your_token_here":
        headers["Authorization"] = f"Bearer {token}"

    return headers


def github_get(endpoint, params=None):
    """Fetch JSON from GitHub and handle common API errors."""
    url = f"{GITHUB_API}/{endpoint.lstrip('/')}"

    try:
        headers = get_headers()

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20,
        )

        # If a configured token is invalid, retry public access
        # without it. This keeps public repository analysis usable.
        if response.status_code == 401 and "Authorization" in headers:
            response = requests.get(
                url,
                headers=BASE_HEADERS,
                params=params,
                timeout=20,
            )

        if response.status_code == 401:
            raise ValueError(
                "GitHub rejected the request. Check your token in "
                ".streamlit/secrets.toml, or remove the invalid token "
                "to use public repository access."
            )

        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining")

            if remaining == "0":
                raise ValueError(
                    "GitHub API rate limit reached. Wait and try again."
                )

            raise ValueError(
                "GitHub denied this request. Try again later."
            )

        if response.status_code == 404:
            raise ValueError(
                "Repository or resource not found. Check the URL "
                "and make sure the repository is public."
            )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout as error:
        raise ValueError(
            "GitHub took too long to respond. Please try again."
        ) from error

    except requests.exceptions.ConnectionError as error:
        raise ValueError(
            "Could not connect to GitHub. Check your internet connection."
        ) from error

    except requests.exceptions.HTTPError as error:
        raise ValueError(
            f"GitHub returned an HTTP error: {error}"
        ) from error


def get_repo_data(repo_url):
    """Get the main repository details."""
    owner, repo = parse_repo_url(repo_url)
    return github_get(f"repos/{owner}/{repo}")


def get_languages(owner, repo):
    """Get language byte counts for a repository."""
    return github_get(f"repos/{owner}/{repo}/languages")


def get_file_tree(owner, repo, branch):
    """Get repository files and folders."""
    encoded_branch = quote(branch, safe="")

    result = github_get(
        f"repos/{owner}/{repo}/git/trees/{encoded_branch}",
        params={"recursive": "1"},
    )

    return result.get("tree", [])


def get_readme(owner, repo):
    """Get and decode the repository README."""
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
    """Get the latest commit details."""
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
    """Get the repository's top contributors."""
    return github_get(
        f"repos/{owner}/{repo}/contributors",
        params={"per_page": limit},
    )


def get_open_issues(owner, repo, limit=20):
    """Get open issues, excluding pull requests."""
    issues = github_get(
        f"repos/{owner}/{repo}/issues",
        params={"state": "open", "per_page": limit},
    )

    return [
        issue for issue in issues
        if "pull_request" not in issue
    ]
