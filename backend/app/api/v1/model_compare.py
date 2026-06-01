"""
多模型对比 API
支持同一 Prompt 并行调用多个模型进行对比
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import get_current_user

router = APIRouter(prefix="/models", tags=["models"])


class CompareRequest(BaseModel):
    """模型对比请求"""
    prompt: str = Field(..., description="测试 Prompt")
    models: List[str] = Field(..., description="模型列表")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2048, ge=1, le=8192)


class ModelResult(BaseModel):
    """单个模型结果"""
    model: str
    response: str
    latency_ms: float
    tokens_used: int
    success: bool
    error: Optional[str] = None


class CompareResponse(BaseModel):
    """对比结果"""
    results: List[ModelResult]
    total_latency_ms: float
    prompt: str


async def _call_model(
    model_name: str,
    prompt: str,
    system_prompt: Optional[str],
    temperature: float,
    max_tokens: int
) -> ModelResult:
    """调用单个模型"""
    start_time = time.time()

    try:
        await asyncio.sleep(0.5)  # 模拟延迟
        latency = (time.time() - start_time) * 1000

        return ModelResult(
            model=model_name,
            response=f"[{model_name}] 这是对 prompt 的响应示例。模型将根据输入生成相应的内容。",
            latency_ms=round(latency, 2),
            tokens_used=150,
            success=True
        )
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return ModelResult(
            model=model_name,
            response="",
            latency_ms=round(latency, 2),
            tokens_used=0,
            success=False,
            error=str(e)
        )


@router.post("/compare", response_model=CompareResponse)
async def compare_models(
    request: CompareRequest,
    current_user: Dict = Depends(get_current_user)
):
    """并行调用多个模型进行对比"""
    start_time = time.time()

    tasks = [
        _call_model(
            model_name=model,
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        for model in request.models
    ]

    results = await asyncio.gather(*tasks)
    total_latency = (time.time() - start_time) * 1000

    return CompareResponse(
        results=list(results),
        total_latency_ms=round(total_latency, 2),
        prompt=request.prompt
    )


@router.get("/compare/presets")
async def get_compare_presets(
    current_user: Dict = Depends(get_current_user)
):
    """获取预设的对比配置"""
    return {
        "presets": [
            {
                "name": "通用对话",
                "prompt": "请解释什么是人工智能",
                "models": ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"],
                "description": "测试模型的通用对话能力"
            },
            {
                "name": "代码生成",
                "prompt": "用 Python 实现快速排序算法",
                "models": ["gpt-4", "claude-3-opus", "gpt-3.5-turbo"],
                "description": "测试模型的代码生成能力"
            },
            {
                "name": "创意写作",
                "prompt": "写一首关于春天的诗",
                "models": ["gpt-4", "claude-3-opus", "gpt-3.5-turbo"],
                "description": "测试模型的创意写作能力"
            },
            {
                "name": "逻辑推理",
                "prompt": "如果所有的猫都怕水，Tom 是一只猫，那么 Tom 怕水吗？请解释推理过程。",
                "models": ["gpt-4", "claude-3-opus", "gpt-3.5-turbo"],
                "description": "测试模型的逻辑推理能力"
            }
        ]
    }


@router.get("/compare/supported")
async def get_supported_models(
    current_user: Dict = Depends(get_current_user)
):
    """获取支持对比的模型列表"""
    return {
        "models": [
            {"id": "gpt-4", "name": "GPT-4", "provider": "openai", "max_tokens": 8192},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai", "max_tokens": 4096},
            {"id": "claude-3-opus", "name": "Claude 3 Opus", "provider": "anthropic", "max_tokens": 4096},
            {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "provider": "anthropic", "max_tokens": 4096},
            {"id": "claude-3-haiku", "name": "Claude 3 Haiku", "provider": "anthropic", "max_tokens": 4096},
            {"id": "llama-3-70b", "name": "Llama 3 70B", "provider": "ollama", "max_tokens": 4096},
            {"id": "qwen-72b", "name": "Qwen 72B", "provider": "ollama", "max_tokens": 4096}
        ]
    }
