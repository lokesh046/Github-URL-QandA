from langchain_google_genai import ChatGoogleGenerativeAI
from api.llm_router import invoke_llm
from config import GEMINI_API_KEY

 
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.2
)
    
def generate_answer(prompt: str):

    response = invoke_llm(prompt)

    return response
    
def answer_question(
        question: str,
        context: str
):

    prompt = f"""
You are a senior software engineer.

Use ONLY the supplied code context to answer.

If the answer cannot be found, say so.

Question:

{question}

Context:

{context}
"""

    response = invoke_llm(prompt)

    return response