
import re

import streamlit as st

from services.github_service import (
    get_repo_data,
    get_languages,
    get_file_tree,
    get_readme,
    get_latest_commit,
    get_contributors,
    get_open_issues,
    parse_repo_url,
    get_file_content,
)

from services.file_explainer import explain_file
from services.github_service import get_text_file_for_qa
from services.repository_qa import search_repository

st.set_page_config(
    page_title="CodeCompass",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 CodeCompass")
st.subheader("Understand any repository. Start contributing with confidence.")
st.write(
    "Explore public GitHub repositories and understand them "
    "in beginner-friendly language."
)

repo_url = st.text_input(
    "GitHub repository URL",
    placeholder="https://github.com/owner/repository",
)

if st.button("Analyze Repository", type="primary"):
    if not repo_url.strip():
        st.warning("Please enter a GitHub repository URL.")
    else:
        try:
            with st.spinner("Analyzing the GitHub repository..."):
                data = get_repo_data(repo_url)
                owner, repo = parse_repo_url(repo_url)

                readme = get_readme(owner, repo)
                languages = get_languages(owner, repo)
                tree = get_file_tree(
                    owner, repo, data["default_branch"]
                )
                latest_commit = get_latest_commit(owner, repo)
                contributors = get_contributors(owner, repo)
                issues = get_open_issues(owner, repo)

            st.session_state["repo_data"] = data
            st.session_state["repo_languages"] = languages
            st.session_state["repo_tree"] = tree
            st.session_state["repo_readme"] = readme
            st.session_state["repo_commit"] = latest_commit
            st.session_state["repo_contributors"] = contributors
            st.session_state["repo_issues"] = issues
            st.session_state["repo_error"] = None

            # Clear previous file-explanation results for the new repository.
            st.session_state.pop("explained_source", None)
            st.session_state.pop("explained_path", None)
            st.session_state.pop("explain_error", None)

        except (ValueError, KeyError) as error:
            st.session_state["repo_error"] = str(error)

        except Exception as error:
            st.session_state["repo_error"] = (
                f"Could not analyze this repository: {error}"
            )

if st.session_state.get("repo_error"):
    st.error(st.session_state["repo_error"])

data = st.session_state.get("repo_data")

if data:
    languages = st.session_state.get("repo_languages", {})
    tree = st.session_state.get("repo_tree", [])
    readme = st.session_state.get("repo_readme")
    latest_commit = st.session_state.get("repo_commit")
    contributors = st.session_state.get("repo_contributors", [])
    issues = st.session_state.get("repo_issues", [])

    st.success("Repository loaded successfully!")

    st.header(f"📦 {data.get('full_name', 'Repository')}")
    st.write(data.get("description") or "No description provided.")

    st.link_button(
        "Open on GitHub",
        data.get("html_url", "https://github.com"),
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⭐ Stars", data.get("stargazers_count", 0))
    col2.metric("🍴 Forks", data.get("forks_count", 0))
    col3.metric("🐛 Open issues", data.get("open_issues_count", 0))
    col4.metric("👥 Watchers", data.get("subscribers_count", 0))

    st.write(
        "**Primary language:**",
        data.get("language") or "Not specified",
    )
    st.write("**Default branch:**", data.get("default_branch", "Unknown"))

    license_info = data.get("license")
    license_name = (
        license_info.get("spdx_id") or license_info.get("name")
        if license_info
        else "Not specified"
    )
    st.write("**License:**", license_name)

    (
        overview_tab,
        files_tab,
        explain_tab,
        qa_tab,
        commits_tab,
        contributors_tab,
        issues_tab,
    ) = st.tabs([
        "📘 Project Explainer",
        "📂 File Explorer",
        "💡 Explain Any File",
        "💬 Repository Q&A",
        "🕒 Latest Commit",
        "👥 Contributors",
        "🐛 Open Issues",
    ])

    # --------------------------------------------------
    # TAB 1: PROJECT EXPLAINER
    # --------------------------------------------------
    with overview_tab:
        st.subheader("Understand This Project")

        if readme:
            lines = readme.splitlines()
            summary_parts = []

            for line in lines:
                cleaned = line.strip()

                if not cleaned:
                    continue
                if cleaned.startswith("#"):
                    continue
                if cleaned.startswith("![") or cleaned.startswith("[!["):
                    continue
                if cleaned.startswith("<"):
                    continue

                summary_parts.append(cleaned)

                if len(" ".join(summary_parts)) >= 700:
                    break

            summary = " ".join(summary_parts)
            summary = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", summary)
            summary = re.sub(r"[*`_]", "", summary)

            st.markdown("### Beginner-friendly overview")

            if summary:
                st.write(summary[:1000])
            else:
                st.info(
                    "The README is available, but a short summary "
                    "could not be extracted automatically."
                )

            with st.expander("Read the full README"):
                st.markdown(readme[:12000])

                if len(readme) > 12000:
                    st.caption(
                        "Preview limited to the first 12,000 characters."
                    )
        else:
            st.info("This repository does not have a readable README.")

        st.markdown("### Programming languages")

        if languages:
            total = sum(languages.values())

            if total:
                percentages = {
                    name: round(count / total * 100, 1)
                    for name, count in languages.items()
                }
                st.bar_chart(percentages)
                st.json(percentages)
            else:
                st.info("Language statistics are unavailable.")
        else:
            st.info("No language statistics were returned.")

        st.markdown("### Suggested starting points")
        st.write(
            "1. Read the README to understand the project's purpose.\n"
            "2. Look for files such as `main.py`, `app.py`, or `index.js`.\n"
            "3. Check `requirements.txt`, `pyproject.toml`, or `package.json` "
            "to discover dependencies.\n"
            "4. Explore the tests folder to see how the project is checked."
        )

    # --------------------------------------------------
    # TAB 2: FILE EXPLORER
    # --------------------------------------------------
    with files_tab:
        st.subheader("Repository File Explorer")

        if tree:
            files = [
                item for item in tree
                if item.get("type") == "blob"
            ]

            search_text = st.text_input(
                "Search files by name",
                key="file_search",
            )

            if search_text:
                files = [
                    item for item in files
                    if search_text.lower() in item["path"].lower()
                ]

            st.caption(f"{len(files)} matching files")

            for item in files[:150]:
                st.text("📄 " + item["path"])

            if len(files) > 150:
                st.caption("Showing the first 150 matching files.")
        else:
            st.info("No repository files were returned.")

    # --------------------------------------------------
    # TAB 3: EXPLAIN ANY FILE
    # --------------------------------------------------
    with explain_tab:
        st.subheader("💡 Explain Any File")
        st.write(
            "Choose a file from the repository to view its code "
            "and understand its purpose in beginner-friendly language."
        )

        supported_extensions = (
            ".py", ".js", ".jsx", ".ts", ".tsx",
            ".html", ".css", ".json", ".yml", ".yaml",
            ".toml", ".md", ".txt",
        )

        if tree:
            source_files = sorted(
                [
                    item["path"]
                    for item in tree
                    if item.get("type") == "blob"
                    and item.get("path", "").lower().endswith(
                        supported_extensions
                    )
                ]
            )

            if source_files:
                selected_path = st.selectbox(
                    "Choose a file to explain",
                    source_files,
                    key="explain_file_path",
                )

                if st.button(
                    "Load and Explain File",
                    type="primary",
                    key="load_explain_file",
                ):
                    try:
                        with st.spinner("Loading file from GitHub..."):
                            owner = data["owner"]["login"]
                            repo = data["name"]

                            source = get_file_content(
                                owner,
                                repo,
                                selected_path,
                                data["default_branch"],
                            )

                        st.session_state["explained_source"] = source
                        st.session_state["explained_path"] = selected_path
                        st.session_state["explain_error"] = None

                    except Exception as error:
                        st.session_state["explain_error"] = str(error)
                        st.session_state.pop("explained_source", None)
                        st.session_state.pop("explained_path", None)

                if st.session_state.get("explain_error"):
                    st.error(st.session_state["explain_error"])

                if (
                    st.session_state.get("explained_path") == selected_path
                    and st.session_state.get("explained_source") is not None
                ):
                    source = st.session_state["explained_source"]
                    explanation = explain_file(selected_path, source)

                    st.divider()
                    st.markdown("### 📝 What this file does")
                    st.write(explanation["purpose"])

                    st.markdown("### 🔍 What was detected")

                    for detail in explanation["details"]:
                        st.write("• " + detail)

                    st.markdown("### 💻 Source code")

                    extension = selected_path.lower().rsplit(".", 1)[-1]

                    language_map = {
                        "py": "python",
                        "js": "javascript",
                        "jsx": "javascript",
                        "ts": "typescript",
                        "tsx": "typescript",
                        "html": "html",
                        "css": "css",
                        "json": "json",
                        "yml": "yaml",
                        "yaml": "yaml",
                        "toml": "toml",
                        "md": "markdown",
                    }

                    st.code(
                        source[:20000],
                        language=language_map.get(extension, "text"),
                    )

                    if len(source) > 20000:
                        st.caption(
                            "The preview shows the first 20,000 characters."
                        )
            else:
                st.info("No supported text files were found in this repository.")
        else:
            st.info("Analyze a repository first to choose a file.")

    # --------------------------------------------------

    # --------------------------------------------------
    # TAB: REPOSITORY Q&A
    # --------------------------------------------------
    with qa_tab:
        st.subheader("💬 Ask Questions About This Repository")
        st.write(
            "Search the repository for relevant code and file locations. "
            "These are keyword-based search results, not AI-generated answers."
        )

        question = st.text_input(
            "What would you like to know?",
            placeholder="Example: Where is the main function?",
            key="repository_qa_question",
        )

        if st.button("Search Repository", key="search_repository_button"):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                try:
                    with st.spinner("Searching repository files..."):
                        owner = data["owner"]["login"]
                        repo = data["name"]
                        branch = data["default_branch"]

                        searchable_extensions = (
                            ".py", ".js", ".jsx", ".ts", ".tsx",
                            ".html", ".css", ".md", ".txt",
                        )

                        candidate_paths = [
                            item["path"]
                            for item in tree
                            if item.get("type") == "blob"
                            and item.get("path", "").lower().endswith(
                                searchable_extensions
                            )
                        ]

                        # Prefer likely entry points and documentation.
                        candidate_paths.sort(
                            key=lambda path: (
                                0 if path.lower().endswith(
                                    ("readme.md", "app.py", "main.py", "index.js")
                                ) else 1,
                                path.lower(),
                            )
                        )

                        # Limit work so a large repository does not trigger
                        # hundreds of GitHub API requests.
                        candidate_paths = candidate_paths[:20]

                        searchable_files = {}
                        file_errors = []

                        for path in candidate_paths:
                            try:
                                content = get_text_file_for_qa(
                                    owner, repo, path, branch
                                )
                                if content:
                                    searchable_files[path] = content
                            except Exception:
                                file_errors.append(path)

                        matches = search_repository(
                            question, searchable_files
                        )

                    st.session_state["qa_matches"] = matches
                    st.session_state["qa_question"] = question
                    st.session_state["qa_error"] = None
                    st.session_state["qa_files_searched"] = len(
                        searchable_files
                    )
                    st.session_state["qa_file_errors"] = len(file_errors)

                except Exception as error:
                    st.session_state["qa_error"] = str(error)

        if st.session_state.get("qa_error"):
            st.error(st.session_state["qa_error"])

        if st.session_state.get("qa_question"):
            st.markdown(
                f"### Search results for: "
                f"{st.session_state['qa_question']}"
            )
            st.caption(
                f"Searched {st.session_state.get('qa_files_searched', 0)} files."
            )

            if st.session_state.get("qa_file_errors", 0):
                st.caption(
                    "Some files could not be loaded; results may be incomplete."
                )

            matches = st.session_state.get("qa_matches", [])

            if matches:
                for match in matches:
                    st.markdown(
                        f"**`{match['path']}` — line "
                        f"{match['line_number']}**"
                    )
                    st.code(match["line"], language="text")
            else:
                st.info(
                    "No matching lines were found in the files searched. "
                    "Try different keywords, or inspect the File Explorer."
                )

    # TAB 4: LATEST COMMIT
    # --------------------------------------------------
    with commits_tab:
        st.subheader("Latest Commit")

        if latest_commit:
            st.write("**Message:**", latest_commit["message"])
            st.write("**Author:**", latest_commit["author"])
            st.write("**Date:**", latest_commit["date"])
            st.write("**Commit ID:**", latest_commit["sha"])

            if latest_commit.get("url"):
                st.link_button(
                    "View commit on GitHub",
                    latest_commit["url"],
                )
        else:
            st.info("No commit history was returned.")

    # --------------------------------------------------
    # TAB 5: CONTRIBUTORS
    # --------------------------------------------------
    with contributors_tab:
        st.subheader("Repository Contributors")

        if contributors:
            for person in contributors:
                login = person.get("login", "Unknown")
                profile_url = person.get("html_url", "")
                contribution_count = person.get("contributions", 0)

                if profile_url:
                    st.markdown(
                        f"- [{login}]({profile_url}) — "
                        f"{contribution_count} contributions"
                    )
                else:
                    st.write(
                        f"- {login} — {contribution_count} contributions"
                    )
        else:
            st.info("No contributors were returned.")

    # --------------------------------------------------
    # TAB 6: OPEN ISSUES
    # --------------------------------------------------
    with issues_tab:
        st.subheader("Open Issues")

        if issues:
            for issue in issues:
                title = issue.get("title", "Untitled")
                issue_url = issue.get("html_url", "")
                issue_number = issue.get("number", "?")

                if issue_url:
                    st.markdown(f"**[#{issue_number} — {title}]({issue_url})**")
                else:
                    st.markdown(f"**#{issue_number} — {title}**")

                labels = [
                    label.get("name", "")
                    for label in issue.get("labels", [])
                ]

                st.caption(
                    "Labels: " + (", ".join(labels) if labels else "None")
                )
        else:
            st.info("There are no open issues to display.")
