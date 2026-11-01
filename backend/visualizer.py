
import os
from graphviz import Digraph


def visualize_dfd(dfd_data, output_name="dfd_diagram"):
    # Save image inside Flask's static folder
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    output_path = os.path.join(static_dir, output_name)

    graph = Digraph("DFD", format="png")

    graph.attr(
        rankdir="LR",
        label=dfd_data.get("title", "Data Flow Diagram"),
        labelloc="t",
        fontsize="18",
        nodesep="0.7",
        ranksep="1.0",
        pad="0.3",
        splines="spline"
    )

    graph.attr(
        "node",
        fontname="Arial",
        fontsize="11",
        style="filled",
        color="#444444"
    )

    graph.attr(
        "edge",
        fontname="Arial",
        fontsize="9",
        arrowsize="0.8"
    )

    nodes = dfd_data.get("nodes", [])
    edges = dfd_data.get("edges", [])

    valid_ids = {node.get("id") for node in nodes}

    # Draw nodes
    for node in nodes:
        node_id = node.get("id")
        label = node.get("label", node_id)
        node_type = node.get("type")

        if not node_id:
            continue

        if node_type == "process":
            graph.node(
                node_id,
                label,
                shape="ellipse",
                fillcolor="#DCEBFF"
            )

        elif node_type == "data_store":
            graph.node(
                node_id,
                label,
                shape="cylinder",
                fillcolor="#DDF5E3"
            )

        elif node_type == "external_entity":
            graph.node(
                node_id,
                label,
                shape="box",
                fillcolor="#FFF0CC"
            )

    # Draw valid edges
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        label = edge.get("label", "")

        if source not in valid_ids or target not in valid_ids:
            print("Skipping invalid edge:", edge)
            continue

        if source == target:
            print("Skipping self-loop edge:", edge)
            continue

        is_foreign_key = (
            "fk" in label.lower()
            or "foreign key" in label.lower()
            or "dept_id" in label.lower()
        )

        is_loop = (
            edge.get("kind") == "loop"
            or edge.get("loop") is True
        )

        if is_foreign_key:
            graph.edge(
                source,
                target,
                label=f"DB relationship: {label}",
                style="dashed",
                color="#777777",
                dir="none"
            )

        elif is_loop:
            # Draw a return edge only when explicitly identified
            graph.edge(
                source,
                target,
                label=label or "Repeat loop",
                style="dashed",
                color="#D97706",
                constraint="false",
                minlen="2"
            )

        else:
            graph.edge(
                source,
                target,
                label=label,
                style="solid",
                color="#333333",
                dir="forward"
            )

    # Locate Graphviz on Windows
    graphviz_path = r"C:\Program Files\Graphviz\bin"

    if os.path.exists(os.path.join(graphviz_path, "dot.exe")):
        os.environ["PATH"] = (
            graphviz_path
            + os.pathsep
            + os.environ.get("PATH", "")
        )

    # Generate PNG
    file_path = graph.render(
        filename=output_path,
        cleanup=True,
        view=False
    )

    print("DFD diagram saved at:", file_path)

    return file_path


if __name__ == "__main__":
    from llm_generator import generate_dfd

    dfd_data = generate_dfd(
        "Generate a DFD for the supplied source code."
    )

    visualize_dfd(dfd_data)
