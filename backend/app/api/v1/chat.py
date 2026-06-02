import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import async_session, get_db
from app.engines.safety_engine.safety import SafetyAction, SafetyEngine, SafetyPolicy
from app.models.base import AgentModel, ConversationModel, MessageModel
from app.schemas.api import ChatCompletionResponse

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    agent_id: str
    messages: list[dict]
    conversation_id: str | None = None
    stream: bool = False


async def _get_agent(db: AsyncSession, agent_id: str, tenant_id: str) -> AgentModel:
    stmt = select(AgentModel).where(
        AgentModel.id == agent_id,
        AgentModel.tenant_id == tenant_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.status not in ("published", "draft"):
        raise HTTPException(status_code=400, detail="Agent is not available for chat")
    return agent


def _build_system_prompt(agent: AgentModel) -> str:
    parts = []
    if agent.system_prompt:
        parts.append(agent.system_prompt)
    return "\n\n".join(parts) if parts else "You are a helpful assistant."


@router.post("/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: Request,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Non-streaming chat completion."""
    agent = await _get_agent(db, body.agent_id, user["tenant_id"])

    # Safety check on last user message
    safety = SafetyEngine(SafetyPolicy(**(agent.safety_config or {})))
    last_msg = body.messages[-1]["content"] if body.messages else ""
    safety_result = await safety.check_input(last_msg)
    if not safety_result.safe:
        raise HTTPException(status_code=400, detail="Content blocked by safety filter")

    # Build messages with system prompt
    system_prompt = _build_system_prompt(agent)
    llm_messages = [{"role": "system", "content": system_prompt}]
    llm_messages.extend(body.messages)

    # Knowledge retrieval: if agent has knowledge bases, retrieve relevant chunks
    citations = []
    kb_ids = agent.knowledge_base_ids if hasattr(agent, 'knowledge_base_ids') and agent.knowledge_base_ids else []
    if kb_ids and last_msg:
        try:
            from app.engines.knowledge_engine.retriever.retriever import HybridRetriever
            for kb_id in kb_ids:
                retriever = HybridRetriever()
                results = await retriever.retrieve(kb_id=kb_id, query=last_msg, top_k=3)
                for r in results:
                    citations.append({
                        "content": r.get("content", "")[:200],
                        "score": r.get("score", 0),
                        "document_id": r.get("document_id", ""),
                        "knowledge_base_id": kb_id,
                    })
                    # Inject retrieved context into system prompt
            if citations:
                context_text = "\n\n".join([f"[Source {i+1}] {c['content']}" for i, c in enumerate(citations)])
                llm_messages[0]["content"] += f"\n\nRelevant knowledge:\n{context_text}"
        except Exception:
            pass  # Retrieval is optional; don't block chat on failure

    # Get LLM adapter from app state
    llm_adapter = getattr(request.app.state, "llm_adapter", None)
    if not llm_adapter:
        # Fallback: return a placeholder when no adapter configured
        return {
            "content": f"[No LLM adapter configured] Agent '{agent.name}' received: {last_msg}",
            "model": agent.model_name or "none",
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        }

    response = await llm_adapter.chat(
        messages=llm_messages,
        model=agent.model_name or "",
        temperature=agent.model_config.get("temperature", 0.7),
        max_tokens=agent.model_config.get("max_tokens", 2000))

    # Safety check on output
    output_safety = await safety.check_output(response.content)
    content = output_safety.filtered_content if output_safety.filtered_content else response.content

    # Save conversation
    if not body.conversation_id:
        conv = ConversationModel(
            tenant_id=user["tenant_id"],
            user_id=user["id"],
            agent_id=agent.id,
            title=last_msg[:50])
        db.add(conv)
        await db.flush()
        conv_id = conv.id
    else:
        conv_id = body.conversation_id

    # Save messages
    db.add(MessageModel(conversation_id=conv_id, tenant_id=user["tenant_id"], role="user", content=last_msg))
    db.add(MessageModel(conversation_id=conv_id, tenant_id=user["tenant_id"], role="assistant", content=content))
    await db.flush()

    return {
        "content": content,
        "model": response.model,
        "usage": response.usage.dict() if hasattr(response.usage, "dict") else response.usage,
        "conversation_id": conv_id,
        "citations": citations,
    }


@router.post("/stream")
async def chat_stream(
    request: Request,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """SSE streaming chat."""
    agent = await _get_agent(db, body.agent_id, user["tenant_id"])

    # Safety check on last user message
    safety = SafetyEngine(SafetyPolicy(**(agent.safety_config or {})))
    last_msg = body.messages[-1]["content"] if body.messages else ""
    safety_result = await safety.check_input(last_msg)
    if not safety_result.safe:
        async def error_generator():
            yield {
                "event": "error",
                "data": json.dumps({"error": "Content blocked by safety filter"}),
            }
        return EventSourceResponse(error_generator())

    # Build messages
    system_prompt = _build_system_prompt(agent)
    llm_messages = [{"role": "system", "content": system_prompt}]
    llm_messages.extend(body.messages)

    # Create/update conversation
    if not body.conversation_id:
        conv = ConversationModel(
            tenant_id=user["tenant_id"],
            user_id=user["id"],
            agent_id=agent.id,
            title=last_msg[:50])
        db.add(conv)
        await db.flush()
        conv_id = conv.id
    else:
        conv_id = body.conversation_id

    db.add(MessageModel(conversation_id=conv_id, tenant_id=user["tenant_id"], role="user", content=last_msg))
    await db.flush()

    llm_adapter = getattr(request.app.state, "llm_adapter", None)

    async def event_generator():
        async with async_session() as db:
            full_response = []
            if not llm_adapter:
                placeholder = f"[No LLM adapter configured] Agent '{agent.name}' received: {last_msg}"
                for chunk in placeholder.split():
                    yield {
                        "event": "message",
                        "data": json.dumps({"content": chunk + " ", "done": False}),
                    }
                    full_response.append(chunk)
                    await asyncio.sleep(0.05)
            else:
                try:
                    async for chunk in llm_adapter.chat_stream(
                        messages=llm_messages,
                        model=agent.model_name or "",
                        temperature=agent.model_config.get("temperature", 0.7),
                        max_tokens=agent.model_config.get("max_tokens", 2000)):
                        yield {
                            "event": "message",
                            "data": json.dumps({"content": chunk.content, "done": False}),
                        }
                        full_response.append(chunk.content)
                except Exception as e:
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": str(e)}),
                    }
                    return

            # Save assistant message
            response_text = "".join(full_response)
            output_safety = await safety.check_output(response_text)
            final_content = output_safety.filtered_content or response_text
            db.add(MessageModel(conversation_id=conv_id, tenant_id=user["tenant_id"], role="assistant", content=final_content))
            await db.commit()

            yield {
                "event": "done",
                "data": json.dumps({"content": "", "done": True, "conversation_id": conv_id}),
            }

    return EventSourceResponse(event_generator())


@router.post("/upload")
async def chat_with_file(
    request: Request,
    agent_id: str = Form(...),
    message: str = Form(""),
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Chat with file attachment (image/document)."""
    agent = await _get_agent(db, agent_id, user["tenant_id"])

    upload_dir = os.environ.get("UPLOAD_DIR", "/app/uploads")
    file_id = str(uuid.uuid4())
    filename = file.filename or "upload.bin"
    ext = Path(filename).suffix.lower()
    upload_path = Path(upload_dir) / user["tenant_id"] / "chat" / file_id
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    file_path = upload_path / f"{file_id}{ext}"

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum 50MB.")
    file_path.write_bytes(content)

    file_info = f"[Attached file: {filename} ({len(content)} bytes)]"
    full_message = f"{message}\n{file_info}" if message else file_info

    safety = SafetyEngine(SafetyPolicy(**(agent.safety_config or {})))
    safety_result = await safety.check_input(full_message)
    if not safety_result.safe:
        raise HTTPException(status_code=400, detail="Content blocked by safety filter")

    system_prompt = _build_system_prompt(agent)
    llm_messages = [{"role": "system", "content": system_prompt}]
    llm_messages.append({"role": "user", "content": full_message})

    llm_adapter = getattr(request.app.state, "llm_adapter", None)
    if not llm_adapter:
        return {
            "content": f"[No LLM adapter configured] Agent '{agent.name}' received: {full_message}",
            "model": agent.model_name or "none",
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "file": {"id": file_id, "filename": filename, "size": len(content)},
        }

    response = await llm_adapter.chat(
        messages=llm_messages,
        model=agent.model_name or "",
        temperature=agent.model_config.get("temperature", 0.7),
        max_tokens=agent.model_config.get("max_tokens", 2000))

    output_safety = await safety.check_output(response.content)
    content_text = output_safety.filtered_content if output_safety.filtered_content else response.content

    if not conversation_id:
        conv = ConversationModel(
            tenant_id=user["tenant_id"],
            user_id=user["id"],
            agent_id=agent.id,
            title=message[:50] if message else filename[:50])
        db.add(conv)
        await db.flush()
        conversation_id = conv.id

    db.add(MessageModel(
        conversation_id=conversation_id,
        role="user",
        content=full_message,
        metadata={"file": {"id": file_id, "filename": filename, "size": len(content)}}))
    db.add(MessageModel(conversation_id=conversation_id, role="assistant", content=content_text))
    await db.flush()

    return {
        "content": content_text,
        "model": response.model,
        "usage": response.usage.dict() if hasattr(response.usage, "dict") else response.usage,
        "conversation_id": conversation_id,
        "file": {"id": file_id, "filename": filename, "size": len(content)},
    }
