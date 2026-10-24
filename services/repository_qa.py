
import re


def search_repository(question, files, max_results=5):
    """
    Search repository text files for lines relevant to a question.
    This is keyword-based search, not AI-generated reasoning.
    """
    words = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", question.lower()))

    # Remove common words that usually do not help search.
    stop_words = {
        "the", "and", "for", "what", "where", "when", "which",
        "does", "this", "that", "how", "can", "you", "are",
        "with", "from", "into", "about", "file", "code",
        "tell", "me", "please", "show", "find",
    }
    keywords = words - stop_words

    if not keywords:
        return []

    results = []

    for path, content in files.items():
        if not isinstance(content, str):
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue

            line_lower = line.lower()
            score = sum(1 for word in keywords if word in line_lower)

            # Give a small bonus when the filename matches a keyword.
            filename = path.rsplit("/", 1)[-1].lower()
            score += sum(1 for word in keywords if word in filename)

            if score:
                results.append({
                    "path": path,
                    "line_number": line_number,
                    "line": line.strip(),
                    "score": score,
                })

    results.sort(key=lambda item: item["score"], reverse=True)

    # Avoid returning multiple duplicate lines.
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
