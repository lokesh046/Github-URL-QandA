# eval_ragas.py
#
# RAG Evaluation Script using Ragas Framework
#
# Prerequisites:
#   pip install ragas datasets langchain-google-genai langchain-openai
#
# Usage:
#   python eval_ragas.py

import os
import time
from dotenv import load_dotenv
from datasets import Dataset

# Load environment variables (.env contains keys for Pinecone, Gemini, OpenRouter)
load_dotenv()

# Import retrieval & generation components from our codebase
from rag.retriever import retrieve_chunks
from api.llm_router import invoke_llm
from config import GEMINI_API_KEY, PINECONE_API_KEY, OPENROUTER_API_KEY
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

# Import Ragas components
try:
    from ragas import evaluate
    from ragas.run_config import RunConfig
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision
    )

    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError as e:
    print(f"Error: Ragas or Datasets packages not found.")
    print("Please install them using: pip install ragas datasets")
    print("Then re-run this script.")
    print(f"Actual Import Error: {e}") 
    exit(1)


# Define a set of test evaluation cases matching files in your indexed repository
EVAL_CASES = [
    {
        "question": "What is the entrypoint of the backend application?",
        "ground_truth": "The backend entrypoint is in backend/app/main.py, which initializes the FastAPI app and includes the routers."
    },
    {
        "question": "Which models does the CustomChatModel define for fallbacks?",
        "ground_truth": "The CustomChatModel initializes Gemini (gemini-2.5-flash) as primary, with DeepSeek (deepseek-chat-v3-0324), Qwen (qwen3-32b), and Mistral (mistral-small-3.2-24b) from OpenRouter as fallbacks."
    },
    {
        "question": "How is the users database initialized?",
        "ground_truth": "The database is initialized via the init_db() function in utils/db.py. If DATABASE_URL is set, it creates a PostgreSQL table qa_users; otherwise, it creates an SQLite database file data/users.db with the same schema."
    }
]

# Set target repository ID for retrieval (Change this to your indexed repository id)
REPO_URL = "https://github.com/lokesh046/neural-mind"
# Convert URL to repo_id
from utils.repo_utils import get_repo_id
REPO_ID = get_repo_id(REPO_URL)

print(f"Starting RAG evaluation pipeline for repo: {REPO_ID}...\n")

questions = []
contexts = []
answers = []
ground_truths = []

for case in EVAL_CASES:
    q = case["question"]
    gt = case["ground_truth"]
    
    print(f"Evaluating Question: '{q}'")
    
    # 1. Retrieve relevant code chunks from Pinecone
    t0 = time.time()
    retrieved = retrieve_chunks(repo_id=REPO_ID, query=q, top_k=4)
    t_retrieval = time.time() - t0
    
    # Format retrieved chunks as list of strings for Ragas contexts
    context_texts = [c["text"] for c in retrieved]
    context_combined = "\n\n".join(context_texts)
    print(f"  -> Retrieved {len(retrieved)} chunks (took {t_retrieval:.2f}s)")
    
    # 2. Generate answer using RAG context
    t0 = time.time()
    prompt = f"""
You are a software engineer assistant. Answer the user question based only on the provided context.

Context:
{context_combined}

Question:
{q}
"""
    answer = invoke_llm(prompt)
    t_generation = time.time() - t0
    print(f"  -> Generated answer (took {t_generation:.2f}s)")
    
    questions.append(q)
    contexts.append(context_texts)
    answers.append(answer)
    ground_truths.append(gt)
    print("-" * 50)

# Build the dataset in the format expected by Ragas
data = {
    "question": questions,
    "contexts": contexts,
    "answer": answers,
    "ground_truth": ground_truths
}
dataset = Dataset.from_dict(data)

# Configure the LLM and Embeddings for Ragas evaluation
# Using OpenRouter Free Llama 3.2 3B model as the primary evaluator
# to avoid API key mismatch / rate limits.
evaluator_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    model="openrouter/free",
    temperature=0.0,
    max_retries=3,
    timeout=60
)
from langchain_core.embeddings import Embeddings

class PineconeLlamaEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        from rag.embedder import embed_texts
        arrays = embed_texts(texts)
        return [arr.tolist() for arr in arrays]

    def embed_query(self, text: str) -> list[float]:
        from rag.embedder import embed_query
        arr = embed_query(text)
        return arr.tolist()

evaluator_embeddings = PineconeLlamaEmbeddings()

print("\nRunning Ragas evaluation using Gemini LLM...")
t0 = time.time()

# Run evaluation
run_config = RunConfig(max_workers=1, timeout=180)
result = evaluate(
    dataset=dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision
    ],
    llm=evaluator_llm,
    embeddings=evaluator_embeddings,
    run_config=run_config,
    raise_exceptions=False
)

print(f"Ragas evaluation completed in {time.time() - t0:.2f}s.\n")

# Print metrics report
print("=================== RAGAS EVALUATION METRICS ===================")
if hasattr(result, "scores") and result.scores:
    for metric in result.scores[0].keys():
        scores = [row[metric] for row in result.scores if row[metric] is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        print(f"{metric:<25}: {avg_score:.4f}")
else:
    # Fallback to direct print if structure differs
    print(result)
print("================================================================")

# Convert to pandas dataframe and save to csv
try:
    df = result.to_pandas()
    csv_path = "ragas_eval_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nDetailed evaluation results saved to '{csv_path}'.")
except Exception as e:
    print(f"Could not save csv: {e}")
