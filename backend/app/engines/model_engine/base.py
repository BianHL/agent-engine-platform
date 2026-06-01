from enum import Enum
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from pydantic import BaseModel


class ModelType(str, Enum):
    LLM = "llm"
    EMBEDDING = "embedding"
    RERANK = "rerank"
    ASR = "asr"
    TTS = "tts"
    OCR = "ocr"
    VISION = "vision"


class LLMCapability(str, Enum):
    CHAT = "chat"
    COMPLETION = "completion"
    FUNCTION_CALLING = "function_calling"
    JSON_MODE = "json_mode"
    VISION = "vision"
    REASONING = "reasoning"
    CODE = "code"
    CHINESE = "chinese"
    ENGLISH = "english"


class EmbeddingCapability(str, Enum):
    TEXT = "text"
    CODE = "code"
    MULTILINGUAL = "multilingual"
    IMAGE = "image"
    CHINESE = "chinese"


class LLMModelConfig(BaseModel):
    provider: str
    model_name: str
    display_name: str
    description: str = ""
    capabilities: list[LLMCapability] = []
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    default_top_p: float = 1.0
    context_window: int = 4096
    max_output_tokens: int = 4096
    input_price: float = 0.0
    output_price: float = 0.0
    enabled: bool = True
    is_default: bool = False


class EmbeddingModelConfig(BaseModel):
    provider: str
    model_name: str
    display_name: str
    description: str = ""
    capabilities: list[EmbeddingCapability] = []
    dimensions: int
    max_input_tokens: int = 8192
    price_per_million: float = 0.0
    enabled: bool = True


class BaseLLMAdapter(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def chat(self, messages: list[dict], model: str, temperature: float = 0.7, max_tokens: int = 4096, **kwargs):
        pass

    @abstractmethod
    async def chat_stream(self, messages: list[dict], model: str, temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> AsyncIterator[str]:
        pass

    async def function_call(self, messages: list[dict], functions: list[dict], model: str, **kwargs):
        raise NotImplementedError


class BaseEmbeddingAdapter(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def embed(self, texts: list[str], model: str, **kwargs) -> list[list[float]]:
        pass


class BaseRerankAdapter(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def rerank(self, query: str, documents: list[str], model: str, top_k: int = 10, **kwargs):
        pass


class BaseASRAdapter(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def transcribe(self, audio_data: bytes, model: str, language: str = "zh", **kwargs):
        pass
