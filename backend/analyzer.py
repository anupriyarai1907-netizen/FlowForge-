
import ast
import re
import sqlglot


SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".js": "javascript",
    ".sql": "sql",
}


def analyze_python(code):
    tree = ast.parse(code)
    functions = []
    operations = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                operations.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                operations.append(node.func.attr)

    return {
        "language": "python",
        "functions": sorted(set(functions)),
        "operations": sorted(set(operations))
    }


def analyze_general_language(code, language):
    """
    Initial lightweight analysis for Java, C, C++ and JavaScript.
    Regex-based extraction is approximate, not a full compiler parser.
    """

    # Remove comments and string literals to reduce false matches.
    cleaned = re.sub(
        r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`',
        '""',
        code
    )
    cleaned = re.sub(r'/\*[\s\S]*?\*/|//[^\n]*', '', cleaned)
    cleaned = re.sub(r'^\s*#.*$', '', cleaned, flags=re.MULTILINE)

    if language == "javascript":
        function_pattern = (
            r'\bfunction\s*\*?\s*([A-Za-z_$]\w*)\s*\('
            r'|(?:\b(?:const|let|var)\s+([A-Za-z_$]\w*)\s*=\s*'
            r'(?:async\s*)?\([^)]*\)\s*=>)'
        )
        call_pattern = r'\b([A-Za-z_$]\w*)\s*\('

    elif language == "java":
        function_pattern = (
            r'\b(?:public|private|protected|static|final|abstract|'
            r'synchronized|native|\s)+\s*'
            r'[\w<>\[\],.?]+\s+([A-Za-z_$]\w*)\s*\([^;{}]*\)\s*'
            r'(?:throws\s+[\w., ]+\s*)?\{'
        )
        call_pattern = r'\b([A-Za-z_$]\w*)\s*\('

    else:
        # C and C++ function definitions (basic syntax).
        function_pattern = (
            r'^[ \t]*(?:[\w:*&<>]+\s+)+'
            r'([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{'
        )
        call_pattern = r'\b([A-Za-z_]\w*)\s*\('

    matches = re.findall(function_pattern, cleaned, re.MULTILINE)

    functions = []
    for match in matches:
        if isinstance(match, tuple):
            functions.extend(item for item in match if item)
        else:
            functions.append(match)

    operations = re.findall(call_pattern, cleaned)

    # Exclude function definitions and common language keywords.
    ignored = {
        "if", "for", "while", "switch", "catch", "return",
        "sizeof", "typeof", "new", "delete", "class",
        "function", "main"
    }
    operations = [
        name for name in operations
        if name not in ignored
    ]

    return {
        "language": language,
        "functions": sorted(set(functions)),
        "operations": sorted(set(operations))
    }


def analyze_code(code, filename):
    extension = "." + filename.rsplit(".", 1)[-1].lower()

    if extension not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    language = SUPPORTED_LANGUAGES[extension]

    if language == "sql":
        return {
            "language": "sql",
            "database_analysis": analyze_database(code)
        }

    if language == "python":
        return analyze_python(code)

    return analyze_general_language(code, language)


def analyze_database(sql_code):
    statements = sqlglot.parse(sql_code, read="mysql")
    tables = {}
    relationships = []

    for statement in statements:
        if not isinstance(statement, sqlglot.exp.Create):
            continue

        if statement.args.get("kind") != "TABLE":
            continue

        schema = statement.this

        if isinstance(schema, sqlglot.exp.Schema):
            table_name = schema.this.name
            columns = schema.expressions
        else:
            table_name = schema.name
            columns = []

        tables[table_name] = [
            column.this.name
            for column in columns
            if isinstance(column, sqlglot.exp.ColumnDef)
        ]

    # Basic FK extraction from CREATE TABLE statements.
    table_pattern = re.compile(
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?:`([^`]+)`|(\w+))\s*\((.*?)\)\s*;',
        re.IGNORECASE | re.DOTALL
    )

    fk_pattern = re.compile(
        r'FOREIGN\s+KEY\s*\(\s*`?(\w+)`?\s*\)\s*'
        r'REFERENCES\s+`?(\w+)`?\s*'
        r'\(\s*`?(\w+)`?\s*\)',
        re.IGNORECASE
    )

    for match in table_pattern.finditer(sql_code):
        source_table = match.group(1) or match.group(2)
        body = match.group(3)

        for fk in fk_pattern.finditer(body):
            relationships.append({
                "from_table": source_table,
                "from_column": fk.group(1),
                "to_table": fk.group(2),
                "to_column": fk.group(3)
            })

    return {
        "tables": tables,
        "relationships": relationships
    }


def analyze_project(source_files, sql_code=""):
    code_analysis = []

    for filename, code in source_files.items():
        if filename.lower().endswith(".sql"):
            continue

        code_analysis.append(
            {
                "filename": filename,
                **analyze_code(code, filename)
            }
        )

    database_result = (
        analyze_database(sql_code) if sql_code.strip()
        else {"tables": {}, "relationships": []}
    )

    return {
        "status": "success",
        "code_analysis": code_analysis,
        "database_analysis": database_result
    }
