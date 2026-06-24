from rag.embedder import embed_texts

texts = [
    "def add(a,b): return a+b",
    "def subtract(a,b): return a-b"
]

vectors = embed_texts(texts)

print(vectors.shape)