
from pathlib import Path
import ast
import re

import sqlglot
from flask import Flask, request, jsonify
from flask_cors import CORS

from analyzer import analyze_project
from chunking import chunk_code
from vector_store import store_chunks, create_sql_chunks, collection
from llm_generator import generate_dfd
from validator import validate_dfd
from visualizer import visualize_dfd

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://flowforge-frontend-etnl.onrender.com",
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    }
)

ALLOWED_EXTENSIONS = {".py", ".java", ".c", ".cpp", ".h", ".hpp", ".js"}



@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DFD Generator</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 850px;
                margin: 35px auto;
                padding: 20px;
                background: #f5f7fb;
                color: #222;
            }
            .card {
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 2px 10px #ddd;
            }
            label { display: block; margin-top: 16px; font-weight: bold; }
            input, button { margin: 8px 0; padding: 10px; box-sizing: border-box; }
            input[type=file], input[type=text] { display: block; width: 100%; }
            button {
                background: #2457c5; color: white; border: 0;
                border-radius: 6px; cursor: pointer; padding: 12px 18px;
            }
            button:disabled { opacity: 0.6; cursor: wait; }
            img { max-width: 100%; margin-top: 15px; border: 1px solid #ddd; }
            pre {
                white-space: pre-wrap; overflow-wrap: anywhere;
                background: #f0f2f5; padding: 12px; border-radius: 6px;
            }
            .error { color: #b00020; }
            .hint { color: #555; font-size: 14px; }
        </style>
    </head>
    <body>
      <div class="card">
        <h1>DFD Generator</h1>
        <p>Upload source-code files and an optional SQL file to generate a Data Flow Diagram.</p>
        <form id="dfdForm">
          <label for="code_files">Source code files</label>
          <input id="code_files" type="file" name="code_files"
                 accept=".py,.java,.c,.cpp,.h,.hpp,.js" multiple required>
          <p class="hint">Supported: Python, Java, C, C++, JavaScript, .h and .hpp</p>

          <label for="sql_file">SQL database file (optional)</label>
          <input id="sql_file" type="file" name="sql_file" accept=".sql">

          <label for="question">What DFD should be generated?</label>
          <input id="question" type="text" name="question"
                 value="Generate a data flow diagram for the uploaded source code and database.">
          <button id="submitButton" type="submit">Generate DFD</button>
        </form>

        <p id="status"></p>
        <div id="result"></div>
      </div>

      <script>
        const form = document.getElementById("dfdForm");
        const statusBox = document.getElementById("status");
        const resultBox = document.getElementById("result");
        const submitButton = document.getElementById("submitButton");

        form.addEventListener("submit", async function(event) {
          event.preventDefault();
          statusBox.textContent = "Generating DFD... Please wait.";
          statusBox.className = "";
          resultBox.innerHTML = "";
          submitButton.disabled = true;

          try {
            const response = await fetch("/generate-dfd", {
              method: "POST",
              body: new FormData(form)
            });
            const data = await response.json();

            if (!response.ok) {
              statusBox.textContent = data.error || "DFD generation failed.";
              statusBox.className = "error";

              if (data.validation_errors) {
                const heading = document.createElement("h3");
                heading.textContent = "Validation errors";
                const pre = document.createElement("pre");
                pre.textContent = data.validation_errors.join("\\n");
                resultBox.append(heading, pre);
              }

              if (data.dfd) {
                const heading = document.createElement("h3");
                heading.textContent = "Generated DFD JSON";
                const pre = document.createElement("pre");
                pre.textContent = JSON.stringify(data.dfd, null, 2);
                resultBox.append(heading, pre);
              }
              return;
            }

            statusBox.textContent = data.message || "DFD generated successfully.";

            const imageHeading = document.createElement("h2");
            imageHeading.textContent = "Generated Diagram";
            const image = document.createElement("img");
            image.alt = "Generated Data Flow Diagram";
            image.src = data.diagram_url + "?t=" + Date.now();
            resultBox.append(imageHeading, image);

            const jsonHeading = document.createElement("h2");
            jsonHeading.textContent = "DFD JSON";
            const pre = document.createElement("pre");
            pre.textContent = JSON.stringify(data.dfd, null, 2);
            resultBox.append(jsonHeading, pre);
          } catch (error) {
            statusBox.textContent = "Could not connect to Flask server. Check the terminal.";
            statusBox.className = "error";
          } finally {
            submitButton.disabled = false;
          }
        });
      </script>
    </body>
    </html>
    """


@app.route("/analyze", methods=["POST"])
def analyze_code():
    uploaded = request.files.get("code_file")
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "No file uploaded"}), 400
    if Path(uploaded.filename).suffix.lower() != ".py":
        return jsonify({"error": "Please upload a .py file"}), 400

    try:
        code = uploaded.read().decode("utf-8")
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

        return jsonify({
            "status": "success",
            "functions": functions,
            "operations": operations
        })
    except SyntaxError as error:
        return jsonify({
            "error": "Invalid Python syntax",
            "line": error.lineno
        }), 400
    except UnicodeDecodeError:
        return jsonify({"error": "Please upload a UTF-8 encoded Python file"}), 400


@app.route("/analyze-sql", methods=["POST"])
def analyze_sql():
    uploaded = request.files.get("sql_file")
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "No SQL file uploaded"}), 400
    if Path(uploaded.filename).suffix.lower() != ".sql":
        return jsonify({"error": "Please upload a .sql file"}), 400

    try:
        sql_code = uploaded.read().decode("utf-8")
        statements = sqlglot.parse(sql_code, read="mysql")
        tables = {}
        relationships = []

        for statement in statements:
            if statement is None or not isinstance(statement, sqlglot.exp.Create):
                continue
            if statement.args.get("kind") != "TABLE":
                continue

            schema = statement.this
            if isinstance(schema, sqlglot.exp.Schema):
                table_name = schema.this.name
                column_definitions = schema.expressions
            else:
                table_name = schema.name
                column_definitions = []

            tables[table_name] = [
                column.this.name for column in column_definitions
                if isinstance(column, sqlglot.exp.ColumnDef)
            ]

        # Extract foreign keys from CREATE TABLE statements.
        create_table_pattern = re.compile(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
            r"(?:`([^`]+)`|(\w+))\s*\((.*?)\)\s*;",
            re.IGNORECASE | re.DOTALL
        )
        fk_pattern = re.compile(
            r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*"
            r"REFERENCES\s+`?(\w+)`?\s*\(([^)]+)\)",
            re.IGNORECASE
        )

        for match in create_table_pattern.finditer(sql_code):
            source_table = match.group(1) or match.group(2)
            for fk_column, parent_table, parent_column in fk_pattern.findall(match.group(3)):
                relationships.append({
                    "from_table": source_table,
                    "from_column": fk_column.strip().strip("`"),
                    "to_table": parent_table.strip(),
                    "to_column": parent_column.strip().strip("`")
                })

        return jsonify({
            "status": "success",
            "tables": tables,
            "relationships": relationships
        })
    except UnicodeDecodeError:
        return jsonify({"error": "Please upload a UTF-8 encoded SQL file"}), 400
    except sqlglot.errors.ParseError as error:
        return jsonify({"error": "Invalid SQL syntax", "details": str(error)}), 400


def read_source_files(uploaded_files):
    """Read and validate uploaded source files; return a filename-to-code dictionary."""
    source_files = {}

    for uploaded in uploaded_files:
        if not uploaded or not uploaded.filename:
            continue

        filename = Path(uploaded.filename).name
        extension = Path(filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported source file: {filename}. "
                f"Supported extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        try:
            code = uploaded.read().decode("utf-8")
        except UnicodeDecodeError as error:
            raise UnicodeDecodeError(
                error.encoding, error.object, error.start, error.end,
                f"{filename} must use UTF-8 encoding"
            ) from error

        # Python is syntax-checked with the built-in parser.
        if extension == ".py":
            ast.parse(code)

        source_files[filename] = code

    if not source_files:
        raise ValueError("Please upload at least one source-code file.")

    return source_files


def read_optional_sql():
    uploaded = request.files.get("sql_file")
    if not uploaded or not uploaded.filename:
        return ""

    if Path(uploaded.filename).suffix.lower() != ".sql":
        raise ValueError("The database file must have a .sql extension.")

    sql_code = uploaded.read().decode("utf-8")
    sqlglot.parse(sql_code, read="mysql")
    return sql_code


@app.route("/analyze-project", methods=["POST"])
def analyze_full_project():
    try:
        uploaded_files = request.files.getlist("code_files")

        # Backward compatibility with the old single-file form.
        if not any(file.filename for file in uploaded_files):
            old_file = request.files.get("code_file")
            if old_file and old_file.filename:
                uploaded_files = [old_file]

        source_files = read_source_files(uploaded_files)
        sql_code = read_optional_sql()
        result = analyze_project(source_files, sql_code)
        return jsonify(result)

    except SyntaxError as error:
        return jsonify({
            "error": "Invalid Python syntax",
            "line": error.lineno
        }), 400
    except sqlglot.errors.ParseError as error:
        return jsonify({"error": "Invalid SQL syntax", "details": str(error)}), 400
    except UnicodeDecodeError as error:
        return jsonify({"error": str(error)}), 400
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        app.logger.exception("Project analysis failed")
        return jsonify({
            "error": "Project analysis failed. Check the Flask terminal."
        }), 500


@app.route("/generate-dfd", methods=["POST"])
def generate_dfd_route():
    try:
        uploaded_files = request.files.getlist("code_files")

        # Backward compatibility with the old single-file form.
        if not any(file.filename for file in uploaded_files):
            old_file = request.files.get("code_file")
            if old_file and old_file.filename:
                uploaded_files = [old_file]

        source_files = read_source_files(uploaded_files)
        sql_code = read_optional_sql()

        all_chunks = []
        for filename, source_code in source_files.items():
            chunks = chunk_code(source_code, filename)
            for chunk in chunks:
                chunk["filename"] = filename
            all_chunks.extend(chunks)

        if sql_code.strip():
            all_chunks.extend(create_sql_chunks(sql_code))

        if not all_chunks:
            return jsonify({"error": "No code or database chunks were found."}), 400

        # Replace the previous upload's chunks with the current project's chunks.
        existing = collection.get()
        if existing.get("ids"):
            collection.delete(ids=existing["ids"])

        store_chunks(all_chunks)

        question = request.form.get(
            "question",
            "Generate a data flow diagram for the uploaded source code and database."
        ).strip()
        if not question:
            question = (
                "Generate a data flow diagram for the uploaded source code "
                "and database."
            )

        dfd_data = generate_dfd(question)
        validation_errors = validate_dfd(dfd_data)

        if validation_errors:
            return jsonify({
                "error": "DFD validation failed",
                "validation_errors": validation_errors,
                "dfd": dfd_data
            }), 422

        visualize_dfd(dfd_data, "dfd_diagram")

        return jsonify({
            "status": "success",
            "message": "DFD generated successfully",
            "dfd": dfd_data,
            "diagram_url": "/static/dfd_diagram.png"
        }), 200

    except SyntaxError as error:
        return jsonify({
            "error": "Invalid Python syntax",
            "line": error.lineno
        }), 400
    except sqlglot.errors.ParseError as error:
        return jsonify({"error": "Invalid SQL syntax", "details": str(error)}), 400
    except UnicodeDecodeError:
        return jsonify({"error": "Files must use UTF-8 encoding."}), 400
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        app.logger.exception("DFD generation failed")
        return jsonify({
            "error": "DFD generation failed. Check the Flask terminal for details."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
