
from embeddings import generate_embedding
from vector_store import get_stored_chunks


def retrieve_context(question, n_results=6):
    chunks = get_stored_chunks()

    if not chunks:
        return []

    query_embedding = generate_embedding(question)

    scored_chunks = []

    for chunk in chunks:
        embedding = chunk["embedding"]

        # Both embeddings are normalized by generate_embedding
        score = sum(
            query_value * chunk_value
            for query_value, chunk_value in zip(
                query_embedding, embedding
            )
        )

        scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)

    selected = [
        chunk for _, chunk in scored_chunks[:n_results]
    ]

    # Preserve the earlier behavior of including all function chunks
    selected_ids = {chunk["id"] for chunk in selected}

    for chunk in chunks:
        if (
            chunk["metadata"].get("type") == "function"
            and chunk["id"] not in selected_ids
        ):
            selected.append(chunk)
            selected_ids.add(chunk["id"])

    return [
        {
            "content": chunk["document"],
            "type": chunk["metadata"].get("type", "unknown"),
            "name": chunk["metadata"].get("name", "unknown"),
            "filename": chunk["metadata"].get("filename", "unknown"),
            "language": chunk["metadata"].get("language", "unknown")
        }
        for chunk in selected
    ]


if __name__ == "__main__":
    question = "Generate a DFD for the user data management system."
    results = retrieve_context(question)

    print("Retrieved chunks:", len(results))

    for item in results:
        print("-" * 40)
        print("Type:", item["type"])
        print("Name:", item["name"])
        print("Content:", item["content"])
