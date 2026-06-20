import os
import requests
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from config import OPENROUTER_API_KEY

@tool
def sample_tool(query: str) -> str:
    """A sample tool to test binding."""
    return f"Result for {query}"

tools = [sample_tool]

# Get the list of free models from the API
url = "https://openrouter.ai/api/v1/models"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    free_models = []
    for model in data.get("data", []):
        pricing = model.get("pricing", {})
        prompt = pricing.get("prompt", "0")
        completion = pricing.get("completion", "0")
        if float(prompt) == 0.0 and float(completion) == 0.0:
            free_models.append(model.get("id"))
else:
    print("Failed to fetch models from API")
    free_models = []

print(f"Testing {len(free_models)} free models...")

successes = []
failures = {}

for model_name in free_models:
    print(f"Testing: {model_name}")
    try:
        llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            model=model_name,
            temperature=0.2,
            max_retries=0,
            timeout=10
        )
        bound = llm.bind_tools(tools)
        res = bound.invoke([HumanMessage(content="Hello, use sample_tool on 'test'")])
        print(f"  -> SUCCESS")
        successes.append((model_name, res))
    except Exception as e:
        err_msg = f"{type(e).__name__}: {e}"
        print(f"  -> FAILED: {err_msg}")
        failures[model_name] = err_msg

print("\n=== SUCCESSFUL MODELS ===")
for model, res in successes:
    print(f"- {model}")

print("\n=== SUMMARY ===")
print(f"Total tested: {len(free_models)}")
print(f"Success count: {len(successes)}")
print(f"Failure count: {len(failures)}")
