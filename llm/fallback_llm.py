from typing import Any, List, Optional
from pydantic import ConfigDict
from langchain_core.runnables import RunnableSerializable, Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

# Import the exact low-level client exception visible in your stack trace
from google.genai.errors import ClientError

from config import GEMINI_API_KEY, OPENROUTER_API_KEY

class FallbackLLM(RunnableSerializable[Any, Any]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    primary_model: Any = None
    cohere: Any = None
    gemma: Any = None
    openrouter_free: Any = None
    runner: Optional[Runnable] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.primary_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.2,
            max_retries=0,
            timeout=10
        )
        self.cohere = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            model="meta-llama/llama-3.2-3b-instruct:free",
            temperature=0.2,
            max_retries=0,
            timeout=15
        )
        self.gemma = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            model="openai/gpt-oss-120b:free",
            temperature=0.2,
            max_retries=0,
            timeout=15
        )
        self.openrouter_free = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            model="openrouter/free",
            temperature=0.2,
            max_retries=0,
            timeout=15
        )
        self.runner = None

    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "FallbackLLM":
        bound_primary = self.primary_model.bind_tools(tools, **kwargs)
        bound_cohere = self.cohere.bind_tools(tools, **kwargs)
        bound_gemma = self.gemma.bind_tools(tools, **kwargs)
        bound_openrouter_free = self.openrouter_free.bind_tools(tools, **kwargs)

        self.runner = bound_primary.with_fallbacks(
            fallbacks=[bound_cohere, bound_gemma, bound_openrouter_free],
            exceptions_to_handle=(ClientError, Exception)
        )
        return self

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Any:
        if not self.runner:
            self.runner = self.primary_model.with_fallbacks(
                fallbacks=[self.cohere, self.gemma, self.openrouter_free],
                exceptions_to_handle=(ClientError, Exception)
            )
        return self.runner.invoke(input, config, **kwargs)

    def stream(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Any:
        if not self.runner:
            self.runner = self.primary_model.with_fallbacks(
                fallbacks=[self.cohere, self.gemma, self.openrouter_free],
                exceptions_to_handle=(ClientError, Exception)
            )
        return self.runner.stream(input, config, **kwargs)
