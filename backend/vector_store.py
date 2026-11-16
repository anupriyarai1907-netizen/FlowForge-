
from analyzer import analyze_database
from embeddings import generate_embeddings


# Lightweight in-memory storage
_stored_chunks = []


class InMemoryCollection:

    def get(self, include=None):
        return {
            "ids": [item["id"] for item in _stored_chunks],
            "documents": [item["document"] for item in _stored_chunks],
            "metadatas": [item["metadata"] for item in _stored_chunks]
        }

    def delete(self, ids):
        global _stored_chunks
        ids_to_delete = set(ids or [])
        _stored_chunks = [
            item for item in _stored_chunks
            if item["id"] not in ids_to_delete
        ]

    def count(self):
        return len(_stored_chunks)


collection = InMemoryCollection()


def store_chunks(chunks):
    if not chunks:
        print("No chunks found.")
        return

    embeddings = generate_embeddings(chunks)

    for i, chunk in enumerate(chunks):
        record_id = f"current_{i}"

        record = {
            "id": record_id,
            "document": chunk.get("content", ""),
            "embedding": embeddings[i],
            "metadata": {
                "type": str(chunk.get("type", "unknown")),
                "name": str(chunk.get("name", "unknown")),
                "filename": str(chunk.get("filename", "unknown")),
                "language": str(chunk.get("language", "unknown"))
            }
        }

        existing_index = next(
            (index for index, item in enumerate(_stored_chunks)
             if item["id"] == record_id),
            None
        )

        if existing_index is None:
            _stored_chunks.append(record)
        else:
            _stored_chunks[existing_index] = record

    print("Stored chunks:", len(chunks))


def get_stored_chunks():
    return list(_stored_chunks)


def create_sql_chunks(sql_code):
    database_info = analyze_database(sql_code)
    chunks = []

    for table_name, columns in database_info.get("tables", {}).items():
        chunks.append({
            "type": "table",
            "name": table_name,
            "content": (
                f"Database table: {table_name}. "
                f"Columns: {', '.join(columns)}"
            ),
            "filename": "database.sql",
            "language": "sql"
        })

    for relation in database_info.get("relationships", []):
        relation_text = str(relation)

        chunks.append({
            "type": "relationship",
            "name": relation_text,
            "content": f"Database relationship: {relation_text}",
            "filename": "database.sql",
            "language": "sql"
        })

    return chunks
