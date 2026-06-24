from rag.chunker import chunk_file


with open("sample.py", "r") as f:
    text = f.read()

chunks = chunk_file(
    text,
    "sample.py"
)

for chunk in chunks:
    print("-" * 50)
    print(chunk)