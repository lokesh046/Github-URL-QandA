import time
from config import GEMINI_API_KEY, OPENROUTER_API_KEY
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

print("GEMINI API KEY exists:", bool(GEMINI_API_KEY))
print("OPENROUTER API KEY exists:", bool(OPENROUTER_API_KEY))

print("\nTesting ChatGoogleGenerativeAI...")
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
        max_retries=0,
        timeout=10,
        transport="rest"
    )
    t0 = time.time()
    res = llm.invoke("Hello, answer with 'succeed'")
    print(f"ChatGoogleGenerativeAI success: {res.content} (took {time.time() - t0:.2f}s)")
except Exception as e:
    print(f"ChatGoogleGenerativeAI failed: {e}")

print("\nTesting ChatOpenAI (OpenRouter)...")
try:
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        model="meta-llama/llama-3.2-3b-instruct:free",
        temperature=0.2,
        max_retries=0,
        timeout=10
    )
    t0 = time.time()
    res = llm.invoke("Hello, answer with 'succeed'")
    print(f"ChatOpenAI success: {res.content} (took {time.time() - t0:.2f}s)")
except Exception as e:
    print(f"ChatOpenAI failed: {e}")
