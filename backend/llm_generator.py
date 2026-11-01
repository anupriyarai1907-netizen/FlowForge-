
import os
import json
from dotenv import load_dotenv
from google import genai
from retrieval import retrieve_context

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY missing. Check your .env file."
    )

client = genai.Client(api_key=api_key)


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

    # 2. Complete DFD generation prompt: 35 rules
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
5. Identify variable initialization where it represents a
   meaningful processing stage.
6. Identify loops and the operations performed inside them.
7. Identify if, else, switch, and other relevant conditions.
8. Identify calculations, counters, accumulators, and updates.
9. Identify output operations and returned results.
10. Keep distinct operations separate when this improves clarity.
11. Group trivial statements when separate nodes add no value.
12. Represent relevant functions and methods as process nodes.
13. Connect caller and callee processes when an actual call exists.
14. Represent users or external systems as external_entity nodes
    only when supported by the source code.
15. Represent real persistent stores as data_store nodes only
    when supported by the source code.
16. Do not invent database tables or database relationships.
17. Connect processes to stores only when the code provides evidence.
18. Use meaningful labels describing the data being transferred.
19. Preserve the actual order of operations supported by the code.
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
33. Keep calculating totals, calculating averages, evaluating
    pass/fail, and printing results as separate processes
    whenever they are distinct operations in the source code.
34. Evaluate pass/fail before output only when the code does so.
35. Explain missing evidence in warnings and return valid JSON
    matching the required schema.

Additional requirements:
- Prefer clear, readable diagrams over excessive node counts.
- Include meaningful operations from every relevant supplied file.
- If multiple files interact, connect them only where evidence exists.
- If no database is present, do not create a data_store node.
- Return only the structured JSON response.
"""

    # 3. Request structured JSON from Gemini
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": {
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
                            "required": [
                                "id",
                                "label",
                                "type"
                            ]
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
                                    "enum": [
                                        "data_flow",
                                        "loop"
                                    ]
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
                "required": [
                    "title",
                    "nodes",
                    "edges",
                    "warnings"
                ]
            }
        }
    )

    # 4. Parse response
    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    try:
        dfd_data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned invalid JSON."
        ) from exc

    # 5. Validate top-level structure
    if not isinstance(dfd_data, dict):
        raise ValueError("DFD response must be a JSON object.")

    for key in ("title", "nodes", "edges", "warnings"):
        if key not in dfd_data:
            raise ValueError(
                f"DFD response is missing required field: {key}"
            )

    nodes = dfd_data["nodes"]
    edges = dfd_data["edges"]
    warnings = dfd_data["warnings"]

    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("Nodes and edges must be lists.")

    if not isinstance(warnings, list):
        raise ValueError("Warnings must be a list.")

    # 6. Validate nodes
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

    # 7. Validate and normalize edges
    valid_edges = []

    for edge in edges:
        if not isinstance(edge, dict):
            warnings.append(
                f"Invalid edge removed: {edge}"
            )
            continue

        source = edge.get("source")
        target = edge.get("target")
        label = edge.get("label")
        kind = edge.get("kind")

        if (
            source not in valid_ids
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

    # 8. Display diagnostics
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
