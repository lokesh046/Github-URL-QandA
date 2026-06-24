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

    tools: List[Any] = []
    bind_kwargs: dict = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = []
        self.bind_kwargs = {}

    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "FallbackLLM":
        self.tools = tools
        self.bind_kwargs = kwargs
        return self

    def _get_runner(self, config: Optional[RunnableConfig]) -> Runnable:
        # Resolve keys from config or fallback to environment variables
        gemini_key = GEMINI_API_KEY
        openrouter_key = OPENROUTER_API_KEY
        if config and "configurable" in config:
            gemini_key = config["configurable"].get("gemini_api_key") or gemini_key
            openrouter_key = config["configurable"].get("openrouter_api_key") or openrouter_key

        # Create clients dynamically
        primary = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_key,
            temperature=0.2,
            max_retries=0,
            timeout=30
        )
        cohere = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            model="meta-llama/llama-3.2-3b-instruct:free",
            temperature=0.2,
            max_retries=0,
            timeout=15
        )
        gemma = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            model="openai/gpt-oss-120b:free",
            temperature=0.2,
            max_retries=0,
            timeout=15
        )
        openrouter_free = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            model="openrouter/free",
            temperature=0.2,
            max_retries=0,
            timeout=15
        )

        # Bind tools dynamically if they were set
        if self.tools:
            primary = primary.bind_tools(self.tools, **self.bind_kwargs)
            cohere = cohere.bind_tools(self.tools, **self.bind_kwargs)
            gemma = gemma.bind_tools(self.tools, **self.bind_kwargs)
            openrouter_free = openrouter_free.bind_tools(self.tools, **self.bind_kwargs)

        return primary.with_fallbacks(
            fallbacks=[cohere, gemma, openrouter_free],
            exceptions_to_handle=(ClientError, Exception)
        )

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Any:
        runner = self._get_runner(config)
        return runner.invoke(input, config, **kwargs)

    def stream(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Any:
        runner = self._get_runner(config)
        return runner.stream(input, config, **kwargs)
