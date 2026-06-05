import json
from typing import AsyncGenerator, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import ConversationModel, MessageModel


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        tenant_id: str,
        user_id: str,
        agent_id: str,
        title: str = "",
    ) -> dict:
        conv = ConversationModel(
            tenant_id=tenant_id,
            user_id=user_id,
            agent_id=agent_id,
            title=title,
        )
        self.db.add(conv)
        await self.db.flush()
        return {"id": conv.id, "agent_id": conv.agent_id}

    async def get(self, conversation_id: str, tenant_id: str) -> Optional[dict]:
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if not conv:
            return None
        return {
            "id": conv.id,
            "tenant_id": conv.tenant_id,
            "user_id": conv.user_id,
            "agent_id": conv.agent_id,
            "title": conv.title,
            "status": conv.status,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        }

    async def list_conversations(
        self, tenant_id: str, user_id: Optional[str] = None, agent_id: Optional[str] = None, page: int = 1, size: int = 20
    ) -> dict:
        filters = [ConversationModel.tenant_id == tenant_id]
        if user_id:
            filters.append(ConversationModel.user_id == user_id)
        if agent_id:
            filters.append(ConversationModel.agent_id == agent_id)

        count_result = await self.db.execute(
            select(func.count()).where(*filters)
        )
        total = count_result.scalar()

        stmt = (
            select(ConversationModel)
            .where(*filters)
            .order_by(ConversationModel.updated_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        convs = result.scalars().all()

        return {
            "items": [
                {
                    "id": c.id,
                    "agent_id": c.agent_id,
                    "title": c.title,
                    "status": c.status,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                }
                for c in convs
            ],
            "total": total,
            "page": page,
            "size": size,
        }

    async def get_messages(self, conversation_id: str, tenant_id: str) -> list:
        stmt = (
            select(MessageModel)
            .where(
                MessageModel.conversation_id == conversation_id,
                MessageModel.tenant_id == tenant_id,
            )
            .order_by(MessageModel.created_at)
        )
        result = await self.db.execute(stmt)
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "metadata": m.metadata,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in result.scalars().all()
        ]

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tenant_id: str = None,
        metadata: dict = None,
    ) -> dict:
        msg = MessageModel(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            role=role,
            content=content,
            meta_info=metadata or {},
        )
        self.db.add(msg)
        await self.db.flush()
        return {"id": msg.id, "role": msg.role}

    async def search(
        self, tenant_id: str, query: str, user_id: Optional[str] = None, page: int = 1, size: int = 20
    ) -> dict:
        """Search conversations by title or message content."""
        from sqlalchemy import or_

        filters = [ConversationModel.tenant_id == tenant_id]
        if user_id:
            filters.append(ConversationModel.user_id == user_id)

        # Find conversation IDs where messages contain the query
        msg_subq = (
            select(MessageModel.conversation_id)
            .where(
                MessageModel.tenant_id == tenant_id,
                MessageModel.content.ilike(f"%{query}%"),
            )
            .distinct()
        )
        msg_result = await self.db.execute(msg_subq)
        msg_conv_ids = set(msg_result.scalars().all())

        # Combine: title match OR message content match
        title_match = ConversationModel.title.ilike(f"%{query}%")
        combined_filters = filters + [or_(title_match, ConversationModel.id.in_(msg_conv_ids) if msg_conv_ids else False)]

        count_result = await self.db.execute(
            select(func.count()).where(*combined_filters)
        )
        total = count_result.scalar()

        stmt = (
            select(ConversationModel)
            .where(*combined_filters)
            .order_by(ConversationModel.updated_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        convs = result.scalars().all()

        return {
            "items": [
                {
                    "id": c.id,
                    "agent_id": c.agent_id,
                    "title": c.title,
                    "status": c.status,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                }
                for c in convs
            ],
            "total": total,
            "page": page,
            "size": size,
        }

    async def delete(self, conversation_id: str, tenant_id: str) -> None:
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            # Delete all messages first
            msg_stmt = select(MessageModel).where(
                MessageModel.conversation_id == conversation_id
            )
            msg_result = await self.db.execute(msg_stmt)
            for msg in msg_result.scalars().all():
                await self.db.delete(msg)

            await self.db.delete(conv)
            await self.db.flush()

    async def _get_context_messages(
        self, conversation_id: str, limit: int = 20
    ) -> list[dict]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        messages.reverse()
        return [{"role": m.role, "content": m.content} for m in messages]

    async def send_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
        llm_adapter,
        tenant_id: str = None,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str = "",
    ) -> AsyncGenerator[dict, None]:
        if not llm_adapter:
            yield {
                "event": "error",
                "data": json.dumps({"error": "No LLM adapter configured"}),
            }
            return

        try:
            await self.add_message(conversation_id, "user", content, tenant_id=tenant_id)
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": f"Failed to save user message: {str(e)}"}),
            }
            return

        try:
            context_messages = await self._get_context_messages(conversation_id)
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": f"Failed to get context: {str(e)}"}),
            }
            return

        llm_messages = []
        if system_prompt:
            llm_messages.append({"role": "system", "content": system_prompt})
        llm_messages.extend(context_messages)

        full_response = []
        try:
            async for chunk in llm_adapter.chat_stream(
                messages=llm_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                chunk_text = chunk.content if hasattr(chunk, "content") else str(chunk)
                full_response.append(chunk_text)
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "content": chunk_text,
                        "conversation_id": conversation_id,
                    }),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }
            return

        response_text = "".join(full_response)
        try:
            assistant_msg = await self.add_message(
                conversation_id, "assistant", response_text, tenant_id=tenant_id
            )
            assistant_msg_id = assistant_msg.get("id", "")
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": f"Failed to save assistant message: {str(e)}"}),
            }
            return

        yield {
            "event": "done",
            "data": json.dumps({
                "conversation_id": conversation_id,
                "message_id": assistant_msg_id,
            }),
        }
