from pinecone import Pinecone
import numpy as np
from config import PINECONE_API_KEY

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Generate embeddings for multiple texts using Pinecone's Integrated Inference API.
    """
    if not texts:
        return np.empty((0, 1024), dtype=np.float32)
    
    embeddings = []
    batch_size = 96
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        res = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=batch_texts,
            parameters={"input_type": "passage"}
        )
        for item in res:
            embeddings.append(item.values)
            
    return np.array(embeddings, dtype=np.float32)

def embed_query(query: str) -> np.ndarray:
    """
    Generate embedding for a single query text using Pinecone's Integrated Inference API.
    """
    if not query:
        return np.zeros((1024,), dtype=np.float32)
    res = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=[query],
        parameters={"input_type": "query"}
    )
    return np.array(res[0].values, dtype=np.float32)