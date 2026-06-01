from elasticsearch import AsyncElasticsearch
from typing import Optional


class ESStore:
    def __init__(self, hosts: str = "localhost:9200"):
        self.hosts = hosts
        self._client: Optional[AsyncElasticsearch] = None

    async def connect(self):
        self._client = AsyncElasticsearch(hosts=self.hosts)

    async def close(self):
        if self._client:
            await self._client.close()

    async def create_index(self, index_name: str):
        body = {
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "content": {"type": "text", "analyzer": "standard"},
                    "metadata": {"type": "object", "enabled": False},
                    "knowledge_base_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "chunk_id": {"type": "keyword"},
                }
            },
        }
        await self._client.indices.create(index=index_name, body=body)

    async def index_document(self, index_name: str, doc_id: str, document: dict):
        await self._client.index(index=index_name, id=doc_id, document=document)

    async def search(
        self,
        index_name: str,
        query: str,
        knowledge_base_id: str = None,
        top_k: int = 5,
    ) -> list[dict]:
        must = [{"match": {"content": query}}]
        if knowledge_base_id:
            must.append({"term": {"knowledge_base_id": knowledge_base_id}})

        body = {
            "query": {"bool": {"must": must}},
            "size": top_k,
            "_source": ["content", "metadata"],
        }
        result = await self._client.search(index=index_name, body=body)
        hits = result["hits"]["hits"]
        return [
            {
                "id": h["_id"],
                "score": h["_score"],
                "content": h["_source"].get("content", ""),
                "metadata": h["_source"].get("metadata", {}),
            }
            for h in hits
        ]

    async def delete(self, index_name: str, doc_id: str):
        await self._client.delete(index=index_name, id=doc_id, ignore=[404])

    async def delete_index(self, index_name: str):
        await self._client.indices.delete(index=index_name, ignore=[404])

    async def bulk_index(self, index_name: str, documents: list[dict]):
        from elasticsearch.helpers import async_bulk

        actions = [{"_index": index_name, "_id": doc["id"], "_source": doc} for doc in documents]
        await async_bulk(self._client, actions)
