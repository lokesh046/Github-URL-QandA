from openai.types.realtime import realtime_transcription_session_create_response
from typing import Any, List
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from pydantic import BaseModel,Field
from config import (
    GEMINI_API_KEY,
    OPENROUTER_API_KEY
)

class CustomChatModel(BaseChatModel):

    gemini: Any = Field(default=None, exclude=True)
    deepseek: Any = Field(default=None, exclude=True)
    qwen: Any = Field(default=None, exclude=True)
    mistral: Any = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.2
        )

        self.deepseek = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            model="deepseek/deepseek-chat-v3-0324:free"
        )

        self.qwen = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            model="qwen/qwen3-32b:free"
        )

        self.mistral = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            model="mistralai/mistral-small-3.2-24b-instruct:free"
        )

    @property
    def _llm_type(self):
        return "fallback-chat-model"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop=None,
        run_manager=None,
        **kwargs
    ):

        models = [
            ("Gemini", self.gemini),
            ("DeepSeek", self.deepseek),
            ("Qwen", self.qwen),
            ("Mistral", self.mistral)
        ]

        last_error = None

        for name, model in models:

            try:

                print(f"Trying {name}")

                response = model.invoke(messages)

                return ChatResult(
                    generations=[
                        ChatGeneration(
                            message=AIMessage(
                                content=response.content
                            )
                        )
                    ]
                )

            except Exception as e:

                print(f"{name} failed")

                last_error = e

        raise Exception(last_error)