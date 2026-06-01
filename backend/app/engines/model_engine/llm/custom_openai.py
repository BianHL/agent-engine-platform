from app.engines.model_engine.llm.openai import OpenAIAdapter


class CustomOpenAIAdapter(OpenAIAdapter):
    """For any OpenAI-compatible API (DeepSeek, Qwen, Moonshot, vLLM, etc.)"""
    pass
