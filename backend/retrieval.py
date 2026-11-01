

from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_or_create_collection(
    name="dfd_knowledge"
)


def retrieve_context(question, n_results=6):
    total_chunks = collection.count()

    if total_chunks == 0:
        return []

    query_embedding = model.encode(question).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, total_chunks)
    )

    retrieved_chunks = []

    documents = results.get("documents") or [[]]
    metadatas = results.get("metadatas") or [[]]

    if documents and documents[0]:
        for document, metadata in zip(
            documents[0],
            metadatas[0]
        ):
            if document and metadata:
                retrieved_chunks.append({
                    "content": document,
                    "type": metadata.get("type", "unknown"),
                    "name": metadata.get("name", "unknown")
                })

    # Include all stored Python function definitions so
    # the generator can inspect calls between functions.
    all_functions = collection.get(
        where={"type": "function"},
        include=["documents", "metadatas"]
    )

    existing_names = {
        (item["type"], item["name"])
        for item in retrieved_chunks
    }

    for document, metadata in zip(
        all_functions.get("documents") or [],
        all_functions.get("metadatas") or []
    ):
        key = (
            metadata.get("type", "unknown"),
            metadata.get("name", "unknown")
        )

        if key not in existing_names:
            retrieved_chunks.append({
                "content": document,
                "type": metadata.get("type", "unknown"),
                "name": metadata.get("name", "unknown")
            })
            existing_names.add(key)

    return retrieved_chunks


if __name__ == "__main__":
    question = "Generate a DFD for the user data management system."

    results = retrieve_context(question)

    print("\nQuestion:", question)
    print("Retrieved chunks:", len(results))

    for item in results:
        print("-" * 40)
        print("Type:", item["type"])
        print("Name:", item["name"])
        print("Content:", item["content"])

