from google import genai
from config import GEMINI_API_KEY
import numpy as np

client = genai.Client(api_key=GEMINI_API_KEY)


def embed_texts(texts: list[str]) -> np.ndarray:
    embeddings = []

    for text in texts:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )

        embeddings.append(response.embeddings[0].values)

    return np.array(embeddings, dtype=np.float32)


def embed_query(query: str) -> np.ndarray:
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query
    )

    return np.array(
        response.embeddings[0].values,
        dtype=np.float32
    )