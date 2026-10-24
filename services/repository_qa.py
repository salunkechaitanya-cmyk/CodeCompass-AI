
import re


def search_repository(question, files, max_results=5):
    """
    Search repository files for code lines relevant to a question.
    Args:
        question: A string containing the user's question.
        files: A dictionary mapping file paths to file contents.
        max_results: Maximum number of matching lines to return.
    """
    if not isinstance(question, str):
        return []

    if not isinstance(files, dict):
        return []

    words = set(
        re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", question.lower())
    )

    stop_words = {
        "the", "and", "for", "what", "where", "when", "which",
        "does", "this", "that", "how", "can", "you", "are",
        "with", "from", "into", "about", "file", "code",
        "tell", "me", "please", "show", "find", "project",
        "explain", "describe", "work",
    }

    keywords = words - stop_words

    if not keywords:
        keywords = words

    results = []

    for path, content in files.items():
        if not isinstance(path, str) or not isinstance(content, str):
            continue

        filename = path.rsplit("/", 1)[-1].lower()

        for line_number, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue

            line_lower = line.lower()

            score = sum(
                1 for word in keywords
                if re.search(r"\b" + re.escape(word) + r"\b", line_lower)
            )

            score += sum(
                2 for word in keywords
                if re.search(r"\b" + re.escape(word) + r"\b", filename)
            )

            if score > 0:
                results.append({
                    "path": path,
                    "line_number": line_number,
                    "line": line.strip(),
                    "score": score,
                })

    results.sort(key=lambda item: item["score"], reverse=True)

    unique_results = []
    seen = set()

    for result in results:
        key = (result["path"], result["line_number"])

        if key not in seen:
            seen.add(key)
            unique_results.append(result)

        if len(unique_results) >= max_results:
            break

    return unique_results
