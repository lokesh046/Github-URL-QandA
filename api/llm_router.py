from llm.fallback_llm import FallbackLLM

fallback_llm = FallbackLLM()

def invoke_llm(prompt: str) -> str:
    """
    Invokes the fallback LLM from fallback_llm.py to get a text response.
    """
    response = fallback_llm.invoke(prompt)
    return response.content