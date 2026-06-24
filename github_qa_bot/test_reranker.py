from rag.retriever import retrieve_chunks
from rag.formatter import format_chunks
from rag.answer_generator import answer_question


question = "What does Hero component do?"

chunks = retrieve_chunks(
    repo_id="lokesh046_portfolio",
    query=question,
    top_k=15
)

context = format_chunks(chunks)

answer = answer_question(
    question=question,
    context=context
)

print(answer)