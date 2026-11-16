
import os
import json
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

from retrieval import retrieve_context


# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY missing. Check your environment variables."
    )


# Gemini client configuration
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=40000)
)


def generate_dfd(question):

    # 1. Retrieve project context
    context_chunks = retrieve_context(question)

    print("Retrieved chunks:", len(context_chunks))

    if not context_chunks:
        raise ValueError(
            "No relevant context found. Store project chunks first."
        )

    context_parts = []

    for item in context_chunks:
        context_parts.append(
            f"File: {item.get('filename', 'unknown')}\n"
            f"Language: {item.get('language', 'unknown')}\n"
            f"Type: {item.get('type', 'unknown')}\n"
            f"Name: {item.get('name', 'unknown')}\n"
            f"Content:\n{item.get('content', '')}"
        )

    context = "\n\n".join(context_parts)

    # 2. DFD generation prompt
    prompt = f"""
You are an expert source-code analyzer and Data Flow Diagram
(DFD) generator.

Generate a detailed, evidence-based DFD using the supplied
source code. Do not rely only on function names.

USER REQUEST:
{question}

PROJECT SOURCE CONTEXT:
{context}

RULES:

1. Analyze the actual supplied source code carefully.
2. Identify the program entry point and relevant functions.
3. Create separate process nodes for meaningful operations.
4. Identify user input and external system interactions.
5. Identify meaningful variable initialization stages.
6. Identify loops and operations performed inside them.
7. Identify if, else, switch, and relevant conditions.
8. Identify calculations, counters, accumulators, and updates.
9. Identify output operations and returned results.
10. Keep distinct operations separate when useful.
11. Group trivial statements when separate nodes add no value.
12. Represent relevant functions and methods as process nodes.
13. Connect caller and callee processes when an actual call exists.
14. Represent users or external systems as external_entity nodes
    only when supported by the source code.
15. Represent persistent stores as data_store nodes only when
    supported by the source code.
16. Do not invent database tables or relationships.
17. Connect processes to stores only when code provides evidence.
18. Use meaningful labels describing transferred data.
19. Preserve the actual order of supported operations.
20. Follow the actual source code, including its bugs.
21. Do not silently correct incorrect conditions or calculations.
22. Do not invent variables, functions, operations, or data flows.
23. Every node ID must be unique, lowercase, and use underscores.
24. Every edge source and target must reference an existing node.
25. Use only process, data_store, and external_entity node types.
26. Every edge must include source, target, label, and kind.
27. Use kind "data_flow" for ordinary data-flow edges.
28. Use kind "loop" only for genuine repeated control-flow edges.
29. Represent a loop return path when supported by the code.
30. Do not create loop edges merely because a node is named "loop".
31. Represent true and false condition branches when supported.
32. Do not invent branch outcomes or unsupported loop exits.
33. Keep calculating totals, averages, evaluating pass/fail,
    and printing results separate when they are distinct operations.
34. Evaluate pass/fail before output only when the code does so.
35. Explain missing evidence in warnings and return valid JSON.

Additional requirements:
- Prefer clear, readable diagrams over excessive node counts.
- Include meaningful operations from every relevant supplied file.
- Connect multiple files only where evidence exists.
- If no database is present, do not create a data_store node.
- Return only the structured JSON response.
"""

    # 3. Structured JSON response schema
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "title": {
                "type": "STRING"
            },
            "nodes": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "id": {
                            "type": "STRING"
                        },
                        "label": {
                            "type": "STRING"
                        },
                        "type": {
                            "type": "STRING",
                            "enum": [
                                "process",
                                "data_store",
                                "external_entity"
                            ]
                        }
                    },
                    "required": ["id", "label", "type"]
                }
            },
            "edges": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "source": {
                            "type": "STRING"
                        },
                        "target": {
                            "type": "STRING"
                        },
                        "label": {
                            "type": "STRING"
                        },
                        "kind": {
                            "type": "STRING",
                            "enum": ["data_flow", "loop"]
                        }
                    },
                    "required": [
                        "source",
                        "target",
                        "label",
                        "kind"
                    ]
                }
            },
            "warnings": {
                "type": "ARRAY",
                "items": {
                    "type": "STRING"
                }
            }
        },
        "required": ["title", "nodes", "edges", "warnings"]
    }

    # 4. Gemini model fallback with automatic retry
    models_to_try = [
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.8-flash"
    ]

    response = None
    last_error = None

    MAX_RETRIES = 2

    retryable_errors = {
        408, 429, 500, 502, 503, 504
    }

    for model_name in models_to_try:

        for attempt in range(MAX_RETRIES):

            try:
                print(
                    f"Trying Gemini model: {model_name} "
                    f"(Attempt {attempt + 1}/{MAX_RETRIES})"
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": response_schema
                    }
                )

                if response and response.text:
                    print(
                        f"Successfully generated DFD using: "
                        f"{model_name}"
                    )
                    break

                print(f"Empty response from {model_name}")
                response = None

            except APIError as exc:

                last_error = exc
                response = None

                error_code = getattr(exc, "code", None)

                try:
                    error_code = int(error_code)
                except (TypeError, ValueError):
                    error_code = None

                print(
                    f"Gemini error for {model_name}: "
                    f"HTTP {error_code} - {exc}"
                )

                if error_code not in retryable_errors:
                    print(
                        "Non-retryable error. "
                        "Trying the next model."
                    )
                    break

            except Exception as exc:

                last_error = exc
                response = None

                print(
                    f"Unexpected error for {model_name}: {exc}"
                )
                break

            if attempt < MAX_RETRIES - 1:
                wait_time = 2 ** (attempt + 1)

                print(
                    f"Retrying {model_name} after "
                    f"{wait_time} seconds..."
                )

                time.sleep(wait_time)

        if response is not None:
            break

    if response is None:
        raise RuntimeError(
            "All configured Gemini models failed after "
            "retry attempts. Please try again later."
        ) from last_error

    # 5. Parse Gemini response
    try:
        dfd_data = json.loads(response.text)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned invalid JSON."
        ) from exc

    # 6. Validate top-level structure
    if not isinstance(dfd_data, dict):
        raise ValueError("DFD response must be a JSON object.")

    for key in ("title", "nodes", "edges", "warnings"):
        if key not in dfd_data:
            raise ValueError(
                f"DFD response is missing required field: {key}"
            )

    if not isinstance(dfd_data["title"], str):
        raise ValueError("DFD title must be a string.")

    nodes = dfd_data["nodes"]
    edges = dfd_data["edges"]
    warnings = dfd_data["warnings"]

    if not isinstance(nodes, list):
        raise ValueError("Nodes must be a list.")

    if not isinstance(edges, list):
        raise ValueError("Edges must be a list.")

    if not isinstance(warnings, list):
        raise ValueError("Warnings must be a list.")

    # 7. Validate nodes
    allowed_types = {
        "process",
        "data_store",
        "external_entity"
    }

    node_ids = []

    for node in nodes:

        if not isinstance(node, dict):
            raise ValueError("Each node must be a JSON object.")

        node_id = node.get("id")
        label = node.get("label")
        node_type = node.get("type")

        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("Every node must have a valid ID.")

        if not isinstance(label, str) or not label.strip():
            raise ValueError(
                f"Node {node_id} must have a valid label."
            )

        if node_type not in allowed_types:
            raise ValueError(
                f"Invalid node type for {node_id}: {node_type}"
            )

        node_ids.append(node_id)

    if len(node_ids) != len(set(node_ids)):
        raise ValueError("Duplicate node IDs were generated.")

    valid_ids = set(node_ids)

    # 8. Validate and normalize edges
    valid_edges = []

    for edge in edges:

        if not isinstance(edge, dict):
            warnings.append("An invalid edge was removed.")
            continue

        source = edge.get("source")
        target = edge.get("target")
        label = edge.get("label")
        kind = edge.get("kind")

        if (
            not isinstance(source, str)
            or not isinstance(target, str)
            or source not in valid_ids
            or target not in valid_ids
            or source == target
            or not isinstance(label, str)
            or not label.strip()
            or kind not in {"data_flow", "loop"}
        ):
            warnings.append(
                f"Invalid edge removed: {edge}"
            )
            continue

        valid_edges.append({
            "source": source,
            "target": target,
            "label": label.strip(),
            "kind": kind
        })

    dfd_data["edges"] = valid_edges

    # 9. Display diagnostics
    print("Nodes:", dfd_data["nodes"])
    print("Edges:", dfd_data["edges"])
    print("Warnings:", dfd_data["warnings"])

    return dfd_data


if __name__ == "__main__":

    result = generate_dfd(
        "Generate a detailed DFD for the supplied project source code."
    )

    print("\nFinal DFD JSON:")
    print(json.dumps(result, indent=4))
