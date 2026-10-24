# 🧭 CodeCompass-AI

**Understand any repository. Start contributing with confidence.**

CodeCompass-AI is a beginner-friendly GitHub repository explorer designed to help students and new developers understand unfamiliar codebases, explore project files, and discover their first open-source contribution.

## 🚀 Features

- **📘 Project Explainer** — Explore repository details and understand what a project does.
- **📊 Repository Insights** — View repository information, programming languages, and project statistics.
- **📂 File Explorer** — Browse the repository's file and folder structure.
- **💡 Explain Any File** — Get beginner-friendly explanations of source code files.
- **💬 Repository Q&A** — Search repository files for relevant code lines to help answer questions.
- **🕒 Latest Commit** — View the latest commit information.
- **👥 Contributors** — Explore contributors to the repository.
- **🐛 Open Issues** — Find open issues that may offer opportunities to contribute.

## 🛠️ Tech Stack

- Python
- Streamlit
- GitHub REST API

## ⚙️ Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/salunkechaitanya-cmyk/CodeCompass-AI.git
cd CodeCompass-AI
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

Your browser should open the CodeCompass-AI application, usually at `http://localhost:8501`.

## 🔑 GitHub API Configuration

CodeCompass-AI uses the GitHub REST API to retrieve repository information. If you configure a GitHub personal access token, keep it private.

For local development, create `.streamlit/secrets.toml`:

```toml
GITHUB_TOKEN = "your_github_token_here"
```

Replace the placeholder with your own token if your application requires one. Never commit this file or publish your token.

If the app works without a token, you can try it without one first. GitHub's unauthenticated API has lower rate limits.

## 🎯 Who Is It For?

- Students learning programming
- Beginner developers exploring GitHub
- First-time open-source contributors
- Hackathon participants learning unfamiliar projects

## 🌱 Future Improvements

- AI-powered code explanations
- Smarter repository question answering
- Guided first-contribution workflows
- User authentication and personalized history
- Improved deployment and user experience

*Some planned improvements may not be implemented yet.*

## 🤝 Contributing

Contributions, ideas, and feedback are welcome! Feel free to open an issue or propose an improvement.

## 📄 License

Check the repository's [LICENSE](LICENSE) file for licensing terms.

---

**Built to make open source easier to understand, one repository at a time.** 🧭
