import asyncio
import re
import logging
from typing import Optional
from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, utility

logger = logging.getLogger(__name__)

# Allowed characters for delete IDs: alphanumeric, dash, underscore
_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class MilvusVectorStore:
    def __init__(self, host: str = "localhost", port: int = 19530):
        self.host = host
        self.port = port
        self._connections = {}

    def _get_collection(self, collection_name: str, dim: int) -> Collection:
        if not utility.has_collection(collection_name):
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.JSON),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            ]
            schema = CollectionSchema(fields=fields)
            collection = Collection(name=collection_name, schema=schema)
            index_params = {"metric_type": "COSINE", "index_type": "IVF_FLAT", "params": {"nlist": 128}}
            collection.create_index(field_name="embedding", index_params=index_params)
        else:
            collection = Collection(name=collection_name)
        collection.load()
        return collection

    async def create_collection(self, collection_name: str, dim: int):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._get_collection, collection_name, dim)

    async def insert(
        self,
        collection_name: str,
        ids: list[str],
        contents: list[str],
        metadatas: list[dict],
        embeddings: list[list[float]],
        dim: int,
    ):
        collection = self._get_collection(collection_name, dim)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, collection.insert, [ids, contents, metadatas, embeddings])
        await loop.run_in_executor(None, collection.flush)

    async def search(
        self,
        collection_name: str,
        query_embedding: list[float],
        top_k: int = 5,
        dim: int = 1536,
    ) -> list[dict]:
        collection = self._get_collection(collection_name, dim)
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["content", "metadata"],
            ),
        )
        output = []
        for hit in results[0]:
            output.append(
                {
                    "id": hit.id,
                    "score": hit.score,
                    "content": hit.entity.get("content", ""),
                    "metadata": hit.entity.get("metadata", {}),
                }
            )
        return output

    async def delete(self, collection_name: str, ids: list[str], dim: int = 1536):
        # Validate each id to prevent injection in Milvus expressions
        for id_val in ids:
            if not isinstance(id_val, str) or not _SAFE_ID_RE.match(id_val):
                raise ValueError(
                    f"Invalid delete ID: '{id_val}'. "
                    "IDs must match pattern [a-zA-Z0-9_-]+"
                )
        collection = self._get_collection(collection_name, dim)
        loop = asyncio.get_event_loop()
        # Build safe expression with quoted string values
        quoted_ids = ", ".join(f'"{id_val}"' for id_val in ids)
        expr = f"id in [{quoted_ids}]"
        await loop.run_in_executor(None, collection.delete, expr)

    async def drop_collection(self, collection_name: str):
        if utility.has_collection(collection_name):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, utility.drop_collection, collection_name)
