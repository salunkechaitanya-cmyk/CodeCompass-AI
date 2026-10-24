
import ast
import re
from pathlib import PurePosixPath


def explain_file(path, source):
    """Create a simple, rule-based explanation of a source file."""
    filename = PurePosixPath(path).name
    extension = PurePosixPath(path).suffix.lower()

    result = {
        "filename": filename,
        "purpose": "",
        "details": [],
    }

    if filename.lower().startswith("readme"):
        result["purpose"] = (
            "This is a README file. It usually introduces the project, "
            "explains how to install it, and describes how to use it."
        )
        return result

    if filename in {
        "requirements.txt",
        "pyproject.toml",
        "package.json",
    }:
        result["purpose"] = (
            "This is a project configuration or dependency file. "
            "It helps developers manage libraries and project settings."
        )
        return result

    if extension == ".py":
        result["purpose"] = (
            "This is a Python source file containing code that Python "
            "can execute."
        )

        try:
            tree = ast.parse(source)

            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [arg.arg for arg in node.args.args]
                    result["details"].append(
                        f"Function `{node.name}` accepts: "
                        f"{', '.join(args) if args else 'no arguments'}."
                    )

                elif isinstance(node, ast.ClassDef):
                    result["details"].append(
                        f"Class `{node.name}` defines a type of object."
                    )

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        names = [item.name for item in node.names]
                    else:
                        names = [node.module or "a module"]

                    result["details"].append(
                        "Imports: " + ", ".join(names) + "."
                    )

            if not result["details"]:
                result["details"].append(
                    "No top-level functions, classes, or imports "
                    "were detected."
                )

        except SyntaxError:
            result["details"].append(
                "Python syntax could not be parsed. The file may be "
                "incomplete or may contain invalid Python syntax."
            )

    elif extension in {".js", ".jsx", ".ts", ".tsx"}:
        result["purpose"] = (
            "This is a JavaScript or TypeScript source file, often used "
            "for application logic or web interfaces."
        )

        functions = re.findall(
            r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(|"
            r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(",
            source,
        )
        names = [first or second for first, second in functions]

        result["details"].append(
            "Detected functions: " + (
                ", ".join(names) if names else "none detected by simple matching"
            ) + "."
        )

    elif extension in {".html", ".css"}:
        result["purpose"] = (
            "This file helps define a web page's structure or visual styling."
        )

    elif extension in {".json", ".yml", ".yaml", ".toml"}:
        result["purpose"] = (
            "This is a structured configuration or data file, commonly "
            "used to store settings or organized information."
        )

    else:
        result["purpose"] = (
            f"This is a `{extension or 'plain-text'}` file. "
            "Its exact purpose depends on the project and its contents."
        )

    result["details"].append(
        f"The file contains approximately {len(source.splitlines())} lines."
    )

    return result
