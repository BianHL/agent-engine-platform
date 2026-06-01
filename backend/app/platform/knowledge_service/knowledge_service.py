from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import KnowledgeBaseModel


class KnowledgeBaseService:
    def __init__(
        self,
        db: AsyncSession,
        vector_store=None,
        es_store=None,
        graph_store=None,
        embedding_adapter=None,
    ):
        self.db = db
        self.vector_store = vector_store
        self.es_store = es_store
        self.graph_store = graph_store
        self.embedding_adapter = embedding_adapter

    async def create(self, tenant_id: str, data: dict) -> dict:
        dimensions = data.get("dimensions", 1536)
        if self.embedding_adapter and data.get("embedding_model"):
            try:
                dimensions = data.get("dimensions", 1536)
            except Exception:
                pass

        kb_id_prefix = f"tenant_{tenant_id}"

        kb = KnowledgeBaseModel(
            tenant_id=tenant_id,
            name=data["name"],
            description=data.get("description", ""),
            embedding_model=data.get("embedding_model", ""),
            embedding_dimensions=dimensions,
            vector_collection=f"{kb_id_prefix}_kb_temp",
            es_index=f"{kb_id_prefix}_kb_temp",
            graph_enabled=data.get("graph_enabled", False),
            chunk_size=data.get("chunk_size", 500),
            chunk_overlap=data.get("chunk_overlap", 50),
            chunking_strategy=data.get("chunking_strategy", "recursive"),
        )
        self.db.add(kb)
        await self.db.flush()

        # Update collection names with actual KB ID
        kb.vector_collection = f"{kb_id_prefix}_kb_{kb.id}"
        kb.es_index = f"{kb_id_prefix}_kb_{kb.id}"

        if self.vector_store:
            await self.vector_store.create_collection(kb.vector_collection, dimensions)
        if self.es_store:
            await self.es_store.create_index(kb.es_index)

        await self.db.flush()
        return {
            "id": kb.id,
            "name": kb.name,
            "vector_collection": kb.vector_collection,
            "es_index": kb.es_index,
        }

    async def get(self, kb_id: str, tenant_id: str) -> Optional[dict]:
        stmt = select(KnowledgeBaseModel).where(
            and_(
                KnowledgeBaseModel.id == kb_id,
                KnowledgeBaseModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        kb = result.scalar_one_or_none()
        if not kb:
            return None
        return {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "embedding_model": kb.embedding_model,
            "embedding_dimensions": kb.embedding_dimensions,
            "vector_collection": kb.vector_collection,
            "es_index": kb.es_index,
            "graph_enabled": kb.graph_enabled,
            "document_count": kb.document_count,
            "status": kb.status,
            "chunk_size": kb.chunk_size,
            "chunk_overlap": kb.chunk_overlap,
            "chunking_strategy": kb.chunking_strategy,
            "created_at": kb.created_at.isoformat() if kb.created_at else None,
            "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
        }

    async def list(self, tenant_id: str, page: int = 1, size: int = 20) -> dict:
        count_result = await self.db.execute(
            select(func.count()).where(KnowledgeBaseModel.tenant_id == tenant_id)
        )
        total = count_result.scalar()

        stmt = (
            select(KnowledgeBaseModel)
            .where(KnowledgeBaseModel.tenant_id == tenant_id)
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        kbs = result.scalars().all()

        return {
            "items": [
                {
                    "id": k.id,
                    "name": k.name,
                    "description": k.description,
                    "document_count": k.document_count,
                    "status": k.status,
                }
                for k in kbs
            ],
            "total": total,
            "page": page,
            "size": size,
        }

    async def delete(self, kb_id: str, tenant_id: str) -> None:
        stmt = select(KnowledgeBaseModel).where(
            and_(
                KnowledgeBaseModel.id == kb_id,
                KnowledgeBaseModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        kb = result.scalar_one_or_none()
        if kb:
            if self.vector_store:
                await self.vector_store.drop_collection(kb.vector_collection)
            if self.es_store:
                await self.es_store.delete_index(kb.es_index)
            await self.db.delete(kb)
            await self.db.flush()
