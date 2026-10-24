
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
from services.repository_qa import search_repository
from services.llm_service import answer_repository_question
from services.contribution_guide import (
    get_beginner_issues,
    search_global_beginner_issues,
    make_contribution_steps,
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="CodeCompass",
    page_icon="🧭",
    layout="wide",
)


# --------------------------------------------------
# DESIGN
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background: #111318;
        color: #f3f4f8;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .cc-hero {
        padding: 34px;
        border: 1px solid #34364a;
        border-radius: 20px;
        background: linear-gradient(125deg, #20243a, #171923 65%, #28203d);
        margin-bottom: 25px;
    }

    .cc-brand {
        color: #b3a5ff;
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 3px;
    }

    .cc-heading {
        font-size: 40px;
        line-height: 1.2;
        font-weight: 800;
        margin-top: 18px;
        color: #ffffff;
    }

    .cc-accent {
        color: #b3a5ff;
    }

    .cc-description {
        color: #c0c4d5;
        font-size: 16px;
        line-height: 1.8;
        max-width: 800px;
        margin-top: 15px;
    }

    div[data-testid="stMetric"] {
        background: #1a1d27;
        border: 1px solid #343746;
        border-radius: 12px;
        padding: 14px;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        background: #191c25;
        border: 1px solid #454b60;
        border-radius: 10px;
    }

    div.stButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 600;
    }

    .cc-card {
        background: #1a1d27;
        border: 1px solid #343746;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def safe_call(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except Exception as error:
        st.error(f"{function.__name__} failed: {error}")
        return None


def show_repository_overview(data):
    if not isinstance(data, dict):
        st.warning("Repository information is unavailable.")
        return

    st.markdown("### 📊 Project Overview")
    st.subheader(data.get("full_name", data.get("name", "Repository")))
    st.write(data.get("description") or "No description provided.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⭐ Stars", data.get("stargazers_count", 0))
    col2.metric("🍴 Forks", data.get("forks_count", 0))
    col3.metric("🐛 Open Issues", data.get("open_issues_count", 0))
    col4.metric("👁 Watchers", data.get("watchers_count", 0))

    col1, col2 = st.columns(2)
    col1.write("**Primary language**")
    col1.write(data.get("language") or "Not specified")
    col2.write("**Default branch**")
    col2.write(data.get("default_branch", "main"))

    if data.get("html_url"):
        st.markdown(f"[View repository on GitHub]({data['html_url']})")


def display_file_tree(tree):
    if not isinstance(tree, list) or not tree:
        st.info("No files were returned.")
        return

    st.caption(f"{len(tree)} file and folder entries")

    search_text = st.text_input(
        "Filter files",
        placeholder="Search README, app.py, src...",
        key="file_filter",
    )

    filtered = [
        item for item in tree
        if isinstance(item, dict)
        and search_text.lower() in item.get("path", "").lower()
    ]

    for item in filtered[:300]:
        icon = "📁" if item.get("type") == "tree" else "📄"
        st.text(f"{icon}  {item.get('path', 'Unknown path')}")


def display_latest_commit(commit):
    if not isinstance(commit, dict):
        st.info("No commit information is available.")
        return

    st.markdown("#### Latest commit message")
    st.write(commit.get("message", "No message"))

    col1, col2 = st.columns(2)
    col1.metric("Commit ID", commit.get("sha") or "Unknown")
    col2.write("**Author**")
    col2.write(commit.get("author") or "Unknown")

    st.write("**Date:**", commit.get("date") or "Unknown")

    if commit.get("url"):
        st.markdown(f"[View commit on GitHub]({commit['url']})")


def display_contributors(people):
    if not isinstance(people, list) or not people:
        st.info("No contributors were found.")
        return

    for person in people:
        if not isinstance(person, dict):
            continue

        username = person.get("login", "Unknown")
        url = person.get("html_url", "")
        contributions = person.get("contributions", 0)

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                if url:
                    st.markdown(f"**[{username}]({url})**")
                else:
                    st.markdown(f"**{username}**")

            with col2:
                st.metric("Contributions", contributions)


def display_issues(issues):
    if not isinstance(issues, list):
        st.warning("GitHub returned an unexpected issues response.")
        return

    if not issues:
        st.success("No open issues found.")
        return

    st.caption(f"{len(issues)} open issues")

    for issue in issues:
        if not isinstance(issue, dict):
            continue

        title = issue.get("title", "Untitled issue")
        number = issue.get("number", "?")
        author = (issue.get("user") or {}).get("login", "Unknown")
        url = issue.get("html_url", "")
        labels = issue.get("labels", [])

        with st.container(border=True):
            st.markdown(f"#### #{number} — {title}")
            st.caption(f"Opened by {author}")

            label_names = [
                label.get("name", "")
                for label in labels
                if isinstance(label, dict) and label.get("name")
            ]

            if label_names:
                st.write("**Labels:** " + ", ".join(label_names))

            st.caption(f"Comments: {issue.get('comments', 0)}")

            if url:
                st.markdown(f"[View issue on GitHub]({url})")


def display_readme(readme):
    if isinstance(readme, str) and readme.strip():
        st.markdown(readme)
    else:
        st.info("This repository does not have an available README.")


def display_answer(answer):
    if isinstance(answer, str):
        st.markdown(answer)
    elif isinstance(answer, dict):
        # Prefer common answer fields instead of rendering raw JSON.
        for key in ("answer", "response", "explanation", "result"):
            if isinstance(answer.get(key), str):
                st.markdown(answer[key])
                return
        st.write(answer)
    else:
        st.write(answer)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

defaults = {
    "cc_repo_url": "",
    "cc_repo_data": None,
    "cc_owner": "",
    "cc_repo": "",
    "cc_branch": "main",
    "cc_file_tree": None,
    "cc_readme": None,
    "cc_latest_commit": None,
    "cc_contributors": None,
    "cc_open_issues": None,
    "cc_beginner_issues": None,
    "cc_file_content": None,
    "cc_current_file": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------------------------
# HOMEPAGE
# --------------------------------------------------

st.markdown(
    """
    <div class="cc-hero">
        <div class="cc-brand">🧭 CODECOMPASS / DEVELOPER TOOLS</div>
        <div class="cc-heading">
            Navigate any codebase.<br>
            <span class="cc-accent">Build with confidence.</span>
        </div>
        <div class="cc-description">
            Explore GitHub repositories, understand source files,
            ask questions about code, and discover your first
            open-source contribution.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 🔗 Connect a GitHub repository")

repo_url = st.text_input(
    "Public GitHub repository URL",
    placeholder="https://github.com/owner/repository",
    key="homepage_repo_url",
)

if st.button("🧭 Analyze Repository", type="primary", use_container_width=True):
    try:
        owner, repo = parse_repo_url(repo_url.strip())
        data = safe_call(get_repo_data, repo_url.strip())

        if isinstance(data, dict):
            st.session_state.cc_repo_url = repo_url.strip()
            st.session_state.cc_owner = owner
            st.session_state.cc_repo = repo
            st.session_state.cc_repo_data = data
            st.session_state.cc_branch = data.get("default_branch") or "main"

            # Reset data belonging to the previously selected repository.
            for key in (
                "cc_file_tree",
                "cc_readme",
                "cc_latest_commit",
                "cc_contributors",
                "cc_open_issues",
                "cc_beginner_issues",
                "cc_file_content",
            ):
                st.session_state[key] = None

            st.success("Repository loaded successfully.")

    except Exception as error:
        st.error(f"Could not analyze this repository: {error}")


# --------------------------------------------------
# EMPTY HOMEPAGE
# --------------------------------------------------

if not st.session_state.cc_repo_data:
    st.markdown("### ✨ What you can do")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🧠 Understand code")
        st.write("Get a beginner-friendly explanation of source files.")

    with col2:
        st.markdown("#### 📂 Explore files")
        st.write("Browse the repository and inspect its file contents.")

    with col3:
        st.markdown("#### 🚀 Start contributing")
        st.write("Explore open issues and learn contribution steps.")


# --------------------------------------------------
# REPOSITORY WORKSPACE
# --------------------------------------------------

if st.session_state.cc_repo_data:

    owner = st.session_state.cc_owner
    repo = st.session_state.cc_repo
    branch = st.session_state.cc_branch

    st.divider()
    st.caption(f"Selected repository: {owner}/{repo}")

    show_repository_overview(st.session_state.cc_repo_data)

    tabs = st.tabs([
        "📁 File Explorer",
        "📄 README",
        "🧾 Latest Commit",
        "👥 Contributors",
        "🐛 Open Issues",
        "✨ First Contributions",
        "🤖 AI Assistant",
    ])

    # FILE EXPLORER
    with tabs[0]:
        st.markdown("### 📁 File Explorer")

        if st.button("Load File Tree", key="load_tree"):
            result = safe_call(get_file_tree, owner, repo, branch)
            if result is not None:
                st.session_state.cc_file_tree = result

        if st.session_state.cc_file_tree is not None:
            display_file_tree(st.session_state.cc_file_tree)

        st.divider()
        st.markdown("### Read a File")

        file_path = st.text_input(
            "Exact file path",
            placeholder="README.md or src/main.py",
            key="cc_file_path",
        )

        if st.button("Read File", key="read_file"):
            if not file_path.strip():
                st.warning("Enter a file path.")
            else:
                content = safe_call(
                    get_file_content,
                    owner,
                    repo,
                    file_path.strip(),
                    branch,
                )

                if isinstance(content, str):
                    st.session_state.cc_file_content = content
                    st.session_state.cc_current_file = file_path.strip()

        if st.session_state.cc_file_content is not None:
            st.markdown(f"#### {st.session_state.cc_current_file}")
            st.code(st.session_state.cc_file_content)

            if st.button("Explain This File", key="explain_file"):
                explanation = safe_call(
                    explain_file,
                    st.session_state.cc_file_content,
                )
                if explanation is not None:
                    st.markdown("### 🧠 Explanation")
                    display_answer(explanation)

    # README
    with tabs[1]:
        st.markdown("### 📄 Project Documentation")

        if st.button("Load README", key="load_readme"):
            result = safe_call(get_readme, owner, repo)
            if result is not None:
                st.session_state.cc_readme = result

        if st.session_state.cc_readme is not None:
            display_readme(st.session_state.cc_readme)

    # LATEST COMMIT
    with tabs[2]:
        st.markdown("### 🧾 Latest Repository Update")

        if st.button("Load Latest Commit", key="load_commit"):
            result = safe_call(get_latest_commit, owner, repo)
            if result is not None:
                st.session_state.cc_latest_commit = result

        if st.session_state.cc_latest_commit is not None:
            display_latest_commit(st.session_state.cc_latest_commit)

    # CONTRIBUTORS
    with tabs[3]:
        st.markdown("### 👥 Project Contributors")

        limit = st.selectbox(
            "Number of contributors",
            [5, 10, 20, 30],
            index=1,
            key="contributor_limit",
        )

        if st.button("Load Contributors", key="load_contributors"):
            result = safe_call(get_contributors, owner, repo, limit)
            if result is not None:
                st.session_state.cc_contributors = result

        if st.session_state.cc_contributors is not None:
            display_contributors(st.session_state.cc_contributors)

    # OPEN ISSUES
    with tabs[4]:
        st.markdown("### 🐛 Open Issues")
        st.caption("Explore reported problems and possible improvements.")

        if st.button("Load Open Issues", key="load_issues"):
            result = safe_call(get_open_issues, owner, repo, 20)
            if result is not None:
                st.session_state.cc_open_issues = result

        if st.session_state.cc_open_issues is not None:
            display_issues(st.session_state.cc_open_issues)

    # FIRST CONTRIBUTIONS
    with tabs[5]:
        st.markdown("### ✨ First Contribution Guide")

        source = st.radio(
            "Search for beginner issues in",
            ["Selected repository", "Other public repositories"],
            key="issue_source",
        )

        issue_limit = st.slider(
            "Maximum issues",
            min_value=3,
            max_value=20,
            value=10,
            key="issue_limit",
        )

        if st.button("Find Beginner Issues", key="find_issues"):
            if source == "Selected repository":
                result = safe_call(
                    get_beginner_issues,
                    owner,
                    repo,
                    issue_limit,
                )
            else:
                result = safe_call(search_global_beginner_issues, issue_limit)

            if result is not None:
                st.session_state.cc_beginner_issues = result

        issues = st.session_state.cc_beginner_issues

        if isinstance(issues, list) and issues:
            issue_options = {}

            for item in issues:
                if isinstance(item, dict):
                    label = (
                        f"#{item.get('number', '?')} — "
                        f"{item.get('title', 'Untitled issue')}"
                    )
                    issue_options[label] = item

            if issue_options:
                selected = st.selectbox(
                    "Choose an issue",
                    list(issue_options.keys()),
                    key="selected_beginner_issue",
                )

                issue = issue_options[selected]
                st.write(issue.get("body") or "No issue description.")

                if issue.get("html_url"):
                    st.markdown(f"[View issue on GitHub]({issue['html_url']})")

                if st.button("Generate Contribution Steps"):
                    steps = safe_call(make_contribution_steps, issue)
                    if steps is not None:
                        st.markdown("### Your Contribution Steps")
                        display_answer(steps)

        elif issues is not None:
            st.info("No beginner issues were returned.")
            if not isinstance(issues, list):
                st.write(issues)

    # AI ASSISTANT
    
    # AI ASSISTANT
    
    # AI ASSISTANT
    with tabs[6]:
        st.markdown("### 🤖 AI Repository Assistant")
        st.caption(
            "Ask questions about the selected GitHub repository."
        )

        question = st.text_area(
            "Your question",
            placeholder="What does this project do?",
            key="cc_ai_question",
        )

        if st.button(
            "Ask CodeCompass AI",
            type="primary",
            key="ask_ai",
        ):
            if not question.strip():
                st.warning("Enter a question first.")

            elif not owner or not repo:
                st.warning("Please analyze a repository first.")

            else:
                try:
                    with st.spinner("Loading repository files..."):
                        tree = get_file_tree(owner, repo, branch)

                        if not isinstance(tree, list):
                            st.error("Could not load the repository file tree.")
                            st.stop()

                        files = {}
                        supported_extensions = (
                            ".py", ".md", ".txt", ".js", ".ts",
                            ".jsx", ".tsx", ".html", ".css",
                            ".json", ".yml", ".yaml", ".toml",
                        )

                        for item in tree:
                            if not isinstance(item, dict):
                                continue

                            path = item.get("path", "")

                            if (
                                item.get("type") == "blob"
                                and path.lower().endswith(supported_extensions)
                            ):
                                content = get_file_content(
                                    owner, repo, path, branch
                                )

                                if (
                                    isinstance(content, str)
                                    and content.strip()
                                ):
                                    files[path] = content

                    if not files:
                        st.warning(
                            "No readable text files were found "
                            "in this repository."
                        )

                    else:
                        with st.spinner("Searching repository..."):
                            results = search_repository(
                                question.strip(),
                                files,
                                max_results=10,
                            )

                        # Use matching lines when available.
                        if results:
                            context_parts = []

                            for result in results:
                                context_parts.append(
                                    f"File: {result['path']}\n"
                                    f"Line {result['line_number']}: "
                                    f"{result['line']}"
                                )

                            context = "\n\n".join(context_parts)

                            st.markdown("### 🔎 Relevant code")

                            for result in results:
                                st.caption(
                                    f"{result['path']} — "
                                    f"line {result['line_number']}"
                                )
                                st.code(result["line"])

                        else:
                            # Fall back to actual repository contents
                            # if keyword search finds no matching lines.
                            context_parts = []

                            for path, content in list(files.items())[:8]:
                                context_parts.append(
                                    f"File: {path}\n{content[:2500]}"
                                )

                            context = "\n\n".join(context_parts)

                            st.info(
                                "No exact keyword matches found. "
                                "The assistant will use available "
                                "repository files to answer."
                            )

                        if not context.strip():
                            st.warning(
                                "No repository context is available "
                                "to answer this question."
                            )
                        else:
                            with st.spinner("Generating AI answer..."):
                                answer = answer_repository_question(
                                    question.strip(),
                                    context,
                                )

                            st.markdown("### 💡 Answer")
                            display_answer(answer)

                except Exception as error:
                    st.error(f"AI Assistant error: {error}")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()
st.caption(
    "🧭 CodeCompass • Understand any repository. "
    "Start contributing with confidence."
)
