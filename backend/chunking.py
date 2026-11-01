
import re
import os


def detect_language(filename):
    extension = os.path.splitext(filename)[1].lower()

    languages = {
        ".py": "python",
        ".java": "java",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
    }

    return languages.get(extension, "unknown")


def chunk_code(source_code, filename="source_code"):
    if not source_code or not source_code.strip():
        return []

    language = detect_language(filename)
    chunks = []

    # Preserve the complete source file as context.
    chunks.append({
        "type": "source_file",
        "name": os.path.basename(filename),
        "filename": os.path.basename(filename),
        "language": language,
        "content": source_code,
    })

    # Extract function and method declarations.
    if language == "python":
        function_pattern = re.compile(
            r"(?m)^[ \t]*def\s+([A-Za-z_]\w*)\s*\([^)]*\).*:"
        )
    else:
        function_pattern = re.compile(
            r"\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*"
            r"(?:throws\s+[^{]+)?\{"
        )

    matches = list(function_pattern.finditer(source_code))
    function_names = set()

    for index, match in enumerate(matches):
        name = match.group(1)

        # Avoid treating control statements as functions.
        if name in {
            "if", "for", "while", "switch", "catch",
            "return", "print", "println", "printf"
        }:
            continue

        start = match.start()

        if language == "python":
            next_match = matches[index + 1] if index + 1 < len(matches) else None
            end = next_match.start() if next_match else len(source_code)
            function_body = source_code[start:end].rstrip()
        else:
            brace_start = source_code.find("{", match.end() - 1)

            if brace_start == -1:
                continue

            depth = 0
            end = brace_start

            for position in range(brace_start, len(source_code)):
                if source_code[position] == "{":
                    depth += 1
                elif source_code[position] == "}":
                    depth -= 1

                    if depth == 0:
                        end = position + 1
                        break

            function_body = source_code[start:end]

        if name not in function_names and function_body.strip():
            chunks.append({
                "type": "function",
                "name": name,
                "filename": os.path.basename(filename),
                "language": language,
                "content": function_body,
            })
            function_names.add(name)

    # Extract important operations and control-flow statements.
    patterns = [
        (
            "input",
            r"\b(?:Scanner|BufferedReader|input|readLine|"
            r"nextInt|nextDouble|nextLine|scanf|input)\b"
        ),
        (
            "loop",
            r"\b(?:for|while|do)\b"
        ),
        (
            "condition",
            r"\b(?:if|else|switch|case)\b"
        ),
        (
            "calculation",
            r"(?:\+\+|--|\+=|-=|\*=|/=|"
            r"(?<![=!<>])=(?!=)|"
            r"\b(?:total|sum|average|avg|count|failedSubjects)\b)"
        ),
        (
            "output",
            r"\b(?:System\.out\.print(?:ln)?|print|println|"
            r"printf|console\.log)\b"
        ),
    ]

    seen_operations = set()

    for line_number, line in enumerate(source_code.splitlines(), start=1):
        stripped = line.strip()

        if not stripped or stripped.startswith("//"):
            continue

        for operation_type, pattern in patterns:
            if re.search(pattern, stripped, re.IGNORECASE):
                key = (operation_type, stripped)

                if key in seen_operations:
                    continue

                seen_operations.add(key)

                chunks.append({
                    "type": operation_type,
                    "name": f"{operation_type}_line_{line_number}",
                    "filename": os.path.basename(filename),
                    "language": language,
                    "content": (
                        f"Source file: {filename}\n"
                        f"Language: {language}\n"
                        f"Line: {line_number}\n"
                        f"Operation type: {operation_type}\n"
                        f"Code:\n{stripped}"
                    ),
                })
    print(
        f"Chunked {filename}: "
        f"{len(chunks)} chunks created"
    )

    return chunks


def chunk_python_code(source_code):
    return chunk_code(source_code, "source.py")
