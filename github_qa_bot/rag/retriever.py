from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX_NAME
from rag.embedder import embed_query

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)


def retrieve_chunks(
        repo_id: str,
        query: str,
        top_k: int 
):
    """
    Retrieve semantically relevant chunks from the Pinecone index filtered by repo_id.
    """
    import time
    print(f"[Timing] [Retriever] Query embedding generation started...")
    t0 = time.time()
    query_embedding = embed_query(query)
    t_embed = time.time() - t0
    print(f"[Timing] [Retriever] Query embedding generated via Pinecone Inference in {t_embed:.4f}s")

    print(f"[Timing] [Retriever] Pinecone vector search started for repo_id '{repo_id}'...")
    t0 = time.time()
    try:
        response = index.query(
            vector=query_embedding.tolist(),
            top_k=top_k,
            include_metadata=True,
            filter={
                "repo_id": {"$eq": repo_id}
            }
        )
        t_query = time.time() - t0
        print(f"[Timing] [Retriever] Pinecone vector search completed in {t_query:.4f}s (returned {len(response.matches)} matches)")
    except Exception as e:
        print(f"Error querying Pinecone for {repo_id}: {e}")
        return []

    chunks = []
    for match in response.matches:
        meta = match.metadata or {}
        chunks.append(
            {
                "text": meta.get("text", ""),
                "file": meta.get("file", ""),
                "fn_name": meta.get("fn_name", ""),
                "start_line": int(meta.get("start_line", 1))
            }
        )

    return chunks
