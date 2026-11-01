
import chromadb
from sentence_transformers import SentenceTransformer
from chunking import chunk_python_code
from analyzer import analyze_database

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_or_create_collection(
    name="dfd_knowledge"
)



def store_chunks(chunks):
    if not chunks:
        print("No chunks found.")
        return

    documents = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(documents).tolist()

    ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        filename = chunk.get("filename", "unknown")
        name = chunk.get("name", "unknown")
        chunk_type = chunk.get("type", "unknown")
        language = chunk.get("language", "unknown")

        ids.append(f"current_{i}")

        metadatas.append({
            "type": chunk_type,
            "name": name,
            "filename": filename,
            "language": language,
        })

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print("Stored chunks:", len(chunks))
    for chunk in chunks:
        print(
            "Stored:",
            chunk.get("filename", "unknown"),
            chunk.get("type", "unknown"),
            chunk.get("name", "unknown"),
        )




def create_sql_chunks(sql_code):
    database_info = analyze_database(sql_code)
    chunks = []

    # Store table names and their columns
    for table_name, columns in database_info.get("tables", {}).items():
        chunks.append({
            "type": "table",
            "name": table_name,
            "content": (
                f"Database table: {table_name}. "
                f"Columns: {', '.join(columns)}"
            )
        })

    # Store foreign-key relationships
    for relation in database_info.get("relationships", []):
        relation_text = str(relation)
        chunks.append({
            "type": "relationship",
            "name": relation_text,
            "content": f"Database relationship: {relation_text}"
        })

    return chunks




if __name__ == "__main__":
    with open("sample.py", "r", encoding="utf-8") as file:
        python_code = file.read()

    with open("sample.sql", "r", encoding="utf-8") as file:
        sql_code = file.read()

    python_chunks = chunk_python_code(python_code)
    sql_chunks = create_sql_chunks(sql_code)

    all_chunks = python_chunks + sql_chunks

    store_chunks(all_chunks)

    print("Python chunks:", len(python_chunks))
    print("SQL chunks:", len(sql_chunks))
    print("Total stored chunks:", collection.count())
