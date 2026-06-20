# pyrefly: ignore [missing-import]
import chromadb
import  hashlib


client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="github_repo_chunks"
)

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

    documents,metadatas,ids=[],[],[]

    for idx, chunk in enumerate(chunks):

        documents.append(
            chunk["text"]
        )

        metadatas.append(
            {
                "repo_id": repo_id,
                "file": chunk["file"],
                "fn_name": chunk["fn_name"] or "",
                "start_line": chunk["start_line"] or 0
            })

        ids.append(
            generate_chunk_id(
                repo_id,
                chunk["file"],
                chunk["fn_name"],
                chunk["text"]
            )
        )

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

def count_chunks():
    return collection.count()

def delete_repo(repo_id: str):

    collection.delete(
        where={
            "repo_id": repo_id
        }
    )



def get_collection():

    return client.get_or_create_collection(
        name="github_repo_chunks"
    )


collection = get_collection()


def reset_collection():

    global collection

    try:

        client.delete_collection(
            "github_repo_chunks"
        )

        print(
            "Old collection deleted."
        )

    except Exception:

        pass

    collection = get_collection()

    print(
        "New collection created."
    )