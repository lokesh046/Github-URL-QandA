from rag.retriever import retrieve_chunks
from utils.repo_utils import get_repo_id

repo_url = "https://github.com/lokesh046/portfolio"

repo_id = get_repo_id(repo_url)

query = "What does Hero component do?"

results = retrieve_chunks(
    repo_id=repo_id,
    query=query,
    top_k=5
)

for result in results:

    print("-"*50)

    print(
        "File:",
        result["file"]
    )

    print(
        "Function:",
        result["fn_name"]
    )

    print()

    print(
        result["text"]
    )