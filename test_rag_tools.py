from tools.rag_tool import search_index


repo_id = "test_repo"

query = "What does multiply do?"

result = search_index(
    repo_id,
    query
)

print(result)