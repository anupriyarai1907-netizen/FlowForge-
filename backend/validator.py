
def validate_dfd(dfd_data):
    errors = []

    nodes = dfd_data.get("nodes", [])
    edges = dfd_data.get("edges", [])

    # Check required sections
    if not dfd_data.get("title"):
        errors.append("DFD title is missing.")

    # Check unique node IDs
    node_ids = [node.get("id") for node in nodes]

    if len(node_ids) != len(set(node_ids)):
        errors.append("Duplicate node IDs found.")

    valid_types = {
        "process",
        "data_store",
        "external_entity"
    }

    for node in nodes:
        if not node.get("id") or not node.get("label"):
            errors.append("A node is missing its ID or label.")

        if node.get("type") not in valid_types:
            errors.append(
                f"Invalid node type for {node.get('id')}."
            )

    # Check whether every edge connects existing nodes
    known_ids = set(node_ids)

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        if source not in known_ids:
            errors.append(
                f"Unknown source node: {source}"
            )

        if target not in known_ids:
            errors.append(
                f"Unknown target node: {target}"
            )

        if not edge.get("label"):
            errors.append("A data flow is missing its label.")

    return errors


if __name__ == "__main__":
    from llm_generator import generate_dfd

    result = generate_dfd(
        "Generate a DFD for the user data management system."
    )

    errors = validate_dfd(result)

    if errors:
        print("Validation failed:")
        for error in errors:
            print("-", error)
    else:
        print("DFD validation successful!")
