from rag.retriever import retrieve_chunks


def format_chunks(chunks):

    context = []

    for chunk in chunks:
        context.append(
            f"""
            File: {chunk['file']}
            Function: {chunk['fn_name']}
            Line: {chunk['start_line']}
            {chunk['text']}
            """
        )

    return "\n".join(context)

def get_repo_id(repo_url: str):
    parts = repo_url.rstrip("/").split("/")


    owner = parts[-2]
    repo = parts[-1]


    return f"{owner}_{repo}"

def search_index(
    repo_url: str,
    question: str,
    top_k: int = 5
):
    repo_id = get_repo_id(repo_url)

    chunks = retrieve_chunks(
        repo_id=repo_id,
        query=question,
        top_k=top_k
    )

    return format_chunks(chunks)

