
from sentence_transformers import SentenceTransformer
from chunking import chunk_python_code


# Load a pretrained embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings(chunks):
    texts = [chunk["content"] for chunk in chunks]

    if not texts:
        return []

    vectors = model.encode(texts)

    results = []

    for chunk, vector in zip(chunks, vectors):
        results.append({
            "name": chunk["name"],
            "content": chunk["content"],
            "embedding": vector.tolist()
        })

    return results


if __name__ == "__main__":
    with open("sample.py", "r", encoding="utf-8") as file:
        code = file.read()

    chunks = chunk_python_code(code)
    embedded_chunks = generate_embeddings(chunks)

    for item in embedded_chunks:
        print("-" * 40)
        print("Function:", item["name"])
        print("Vector dimensions:", len(item["embedding"]))
        print("First 5 values:", item["embedding"][:5])
