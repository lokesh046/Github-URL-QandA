from rag.indexer import collection
from rag.embedder import embed_query


def retrieve_chunks(repo_id: str,query: str, top_k=5):

    query_embedding = embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        where={"repo_id": repo_id},
        n_results=top_k
    )


    chunks = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    for doc, meta in zip(documents, metadatas):

        chunks.append(
            {
                "text": doc,
                "file": meta["file"],
                "fn_name": meta["fn_name"],
                "start_line": meta["start_line"]
            }
        )

    return chunks


    

    

    