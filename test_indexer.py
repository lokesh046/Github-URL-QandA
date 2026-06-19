from rag.chunker import chunk_file
from rag.embedder import embed_texts
from rag.indexer import add_chunk,count_chunks,delete_repo


repo_id = "test_repo"


with open("sample.py","r") as f:
    text = f.read()

chunks = chunk_file(
    text,
    "sample.py"
)

text = [
    chunk["text"] for chunk in chunks
]

embedding = embed_texts(text)

delete_repo(repo_id)

add_chunk(chunks,embedding,repo_id)


print("total_chunks",count_chunks())

