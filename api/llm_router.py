from openai import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from config import (
    GEMINI_API_KEY,
    OPENROUTER_API_KEY
)

gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.2
)

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

FALLBACK_MODELS = [

    "deepseek/deepseek-chat-v3-0324:free",

    "qwen/qwen3-32b:free",

    "mistralai/mistral-small-3.2-24b-instruct:free"

]

def invoke_llm(prompt: str):

    try:

        response = gemini.invoke(prompt)

        return response.content

    except Exception as e:

        if (
            "429" in str(e)
            or
            "RESOURCE_EXHAUSTED" in str(e)
        ):

            print("Gemini quota exceeded.")

            for model in FALLBACK_MODELS:

                try:

                    print(f"Trying {model}")

                    response = (
                        openrouter_client.chat.completions.create(
                            model=model,
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        )
                    )

                    return (
                        response
                        .choices[0]
                        .message
                        .content
                    )

                except Exception:

                    continue

        raise e