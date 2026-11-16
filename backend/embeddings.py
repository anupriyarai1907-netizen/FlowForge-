
import hashlib
import re
from collections import Counter

DIMENSIONS = 256

def generate_embedding(text):
    """Generate a lightweight deterministic embedding without loading PyTorch."""
    vector = [0.0] * DIMENSIONS
    words = re.findall(r"\w+", str(text).lower())

    for word in words:
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % DIMENSIONS
        vector[index] += 1.0

    magnitude = sum(value * value for value in vector) ** 0.5

    if magnitude:
        vector = [value / magnitude for value in vector]

    return vector


def generate_embeddings(chunks):
    return [
        generate_embedding(chunk.get("content", "") if isinstance(chunk, dict) else str(chunk))
        for chunk in chunks
    ]
