import hashlib
from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX_NAME

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)


def generate_chunk_id(
        repo_id: str,
        file_path: str,
        fn_name: str,
        text: str
):
    key = (
        repo_id
        + file_path
        + str(fn_name)
        + text
    )

    return hashlib.md5(
        key.encode("utf-8")
    ).hexdigest()


def add_chunk(chunks: list, embeddings, repo_id: str):
    """
    Upserts document chunks and their local embeddings into the Pinecone index.
    Metadata includes the repo_id, file path, function name, start line, and the raw text chunk.
    """
    vectors = []
    for idx, chunk in enumerate(chunks):
        vector_id = generate_chunk_id(
            repo_id,
            chunk["file"],
            chunk["fn_name"],
            chunk["text"]
        )
        vectors.append({
            "id": vector_id,
            "values": embeddings[idx].tolist(),
            "metadata": {
                "repo_id": repo_id,
                "file": chunk["file"],
                "fn_name": chunk["fn_name"] or "",
                "start_line": int(chunk["start_line"] or 1),
                "text": chunk["text"]
            }
        })

    # Batch upserts (Pinecone recommends batches of ~100 vectors)
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        try:
            index.upsert(vectors=batch)
        except Exception as e:
            raise RuntimeError(f"Failed to upsert to Pinecone: {e}")


def count_chunks() -> int:
    """
    Return the total vector count from the Pinecone index stats.
    """
    try:
        stats = index.describe_index_stats()
        return stats.total_vector_count
    except Exception:
        return 0


def delete_repo(repo_id: str):
    """
    Delete all vectors matching the repo_id metadata filter.
    """
    try:
        index.delete(filter={"repo_id": {"$eq": repo_id}})
    except Exception as e:
        print(f"Error deleting Pinecone vectors for {repo_id}: {e}")


def reset_collection():
    """
    Delete all vectors in the Pinecone index.
    """
    try:
        index.delete(delete_all=True)
        print("All vectors in Pinecone index deleted.")
    except Exception as e:
        print(f"Error resetting Pinecone index: {e}")