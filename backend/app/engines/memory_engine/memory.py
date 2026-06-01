import asyncio
import math
import re
import time
import uuid
import json
from collections import Counter
from typing import Optional
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# 简单停用词表（中英文混合，用于主题提取）
# ---------------------------------------------------------------------------
_STOPWORDS: set[str] = {
    # English
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "about", "up",
    "its", "it", "he", "she", "they", "them", "his", "her", "their",
    "this", "that", "these", "those", "i", "me", "my", "we", "you", "your",
    "what", "which", "who", "whom",
    # Chinese
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
    "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些", "什么",
    "吗", "呢", "吧", "啊", "嗯", "哦", "呀", "哈", "么", "把", "被", "让",
    "给", "对", "还", "但", "而", "与", "或", "及", "等", "以", "为", "之",
    "所以", "因为", "但是", "然后", "如果", "虽然", "可以", "可能", "需要",
    "已经", "应该", "能够", "这个", "那个",
}

# 用于切分中英文混合文本的正则：匹配连续英文/数字 或 单个中文字符
_TOKEN_RE = re.compile(r"[a-zA-Z]{2,}|\d+|[一-鿿]")


class ShortTermMemory:
    """Redis-based short-term memory (conversation history)"""

    def __init__(self, redis_client, max_messages: int = 20, ttl: int = 3600):
        self.redis = redis_client
        self.max_messages = max_messages
        self.ttl = ttl

    async def add_message(self, session_id: str, role: str, content: str, metadata: dict = None):
        key = f"memory:short:{session_id}"
        message = json.dumps({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time()
        })
        await self.redis.lpush(key, message)
        await self.redis.ltrim(key, 0, self.max_messages - 1)
        await self.redis.expire(key, self.ttl)

    async def get_messages(self, session_id: str, limit: int = 20) -> list[dict]:
        key = f"memory:short:{session_id}"
        messages = await self.redis.lrange(key, 0, limit - 1)
        return [json.loads(m) for m in messages]

    async def clear(self, session_id: str):
        key = f"memory:short:{session_id}"
        await self.redis.delete(key)


class LongTermMemory:
    """MySQL + Vector-based long-term memory"""

    def __init__(self, db_session, vector_store, embedding_adapter):
        self.db = db_session
        self.vector_store = vector_store
        self.embedding_adapter = embedding_adapter

    async def extract_and_store(self, session_id: str, tenant_id: str, user_id: str, messages: list[dict], llm_adapter=None):
        if not llm_adapter or len(messages) < 3:
            return

        # Use LLM to extract important information
        conversation = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-6:]])
        prompt = f"""从以下对话中提取用户的偏好、重要事实和事件，以JSON数组格式返回：
[{{"type": "preference|fact|event", "content": "提取的内容", "importance": 0.0-1.0}}]

对话：
{conversation}"""

        _MAX_MEMORIES = 10
        _MAX_CONTENT_LEN = 500

        try:
            response = await llm_adapter.chat(
                messages=[{"role": "user", "content": prompt}],
                model=None, temperature=0.1, max_tokens=1000
            )
            content = response.content
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                memories = json.loads(content[start:end])

                # Limit parsed memories to prevent abuse
                for mem in memories[:_MAX_MEMORIES]:
                    try:
                        if not isinstance(mem, dict):
                            continue
                        mem_content = mem.get("content", "")
                        if not isinstance(mem_content, str) or not mem_content.strip():
                            continue
                        # Truncate content to max length
                        mem_content = mem_content[:_MAX_CONTENT_LEN]

                        # Store in vector DB
                        embedding = await self.embedding_adapter.embed([mem_content], model=None)
                        if embedding:
                            await self.vector_store.insert(
                                collection_name=f"memory_{tenant_id}",
                                ids=[f"{user_id}_{int(time.time()*1000)}"],
                                contents=[mem_content],
                                metadatas=[{"type": mem.get("type", "fact"), "user_id": user_id, "importance": mem.get("importance", 0.5)}],
                                embeddings=embedding,
                                dim=len(embedding[0])
                            )
                    except Exception:
                        # Skip malformed entries without crashing
                        continue
        except Exception:
            pass  # Non-critical, don't fail the conversation

    async def search(self, query: str, tenant_id: str, user_id: str, top_k: int = 5) -> list[dict]:
        """基于嵌入向量的语义搜索，使用余弦相似度检索长期记忆"""
        try:
            query_embedding = await self.embedding_adapter.embed([query], model=None)
            if not query_embedding:
                return []

            results = await self.vector_store.search(
                collection_name=f"memory_{tenant_id}",
                query_embedding=query_embedding[0],
                top_k=top_k,
                dim=len(query_embedding[0])
            )
            # 按 user_id 过滤，只返回当前用户的记忆
            filtered = [
                r for r in results
                if r.get("metadata", {}).get("user_id") == user_id
            ]
            # 按相似度分数排序（降序）
            filtered.sort(key=lambda r: r.get("score", 0.0), reverse=True)
            return filtered
        except Exception:
            return []


class WorkingMemory:
    """LLM-compressed working memory for active context"""

    def __init__(self, redis_client, max_tokens: int = 2000):
        self.redis = redis_client
        self.max_tokens = max_tokens

    async def compress(self, session_id: str, messages: list[dict], llm_adapter=None):
        if not llm_adapter or len(messages) < 5:
            return

        conversation = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        prompt = f"""将以下对话压缩为简洁摘要，保留关键信息和上下文，控制在500字以内：

{conversation}"""

        try:
            response = await llm_adapter.chat(
                messages=[{"role": "user", "content": prompt}],
                model=None, temperature=0.1, max_tokens=500
            )
            key = f"memory:working:{session_id}"
            await self.redis.set(key, response.content, ex=7200)
        except Exception:
            pass

    async def get_summary(self, session_id: str) -> str:
        key = f"memory:working:{session_id}"
        summary = await self.redis.get(key)
        return summary if summary else ""


class EpisodicMemory:
    """对话片段的结构化记忆存储，支持语义检索

    每个租户使用独立的向量集合，确保数据隔离。
    """

    def __init__(self, redis_client, embedding_adapter=None, vector_store=None, tenant_id: str = "default"):
        self.redis = redis_client
        self.embedding_adapter = embedding_adapter
        self.vector_store = vector_store
        self.tenant_id = tenant_id
        self._collection_name = f"episodic_memory_{tenant_id}"

    async def store(
        self,
        episode_id: str,
        conversation_id: str,
        summary: str,
        key_facts: list[str],
        user_id: str = "",
        timestamp: Optional[float] = None,
    ) -> str:
        """存储一个对话片段，同时写入向量库用于后续语义检索"""
        if timestamp is None:
            timestamp = time.time()

        episode = {
            "episode_id": episode_id,
            "conversation_id": conversation_id,
            "summary": summary,
            "key_facts": key_facts,
            "timestamp": timestamp,
        }

        # 存入 Redis
        key = f"memory:episodic:{self.tenant_id}:{episode_id}"
        await self.redis.set(key, json.dumps(episode, ensure_ascii=False), ex=86400 * 30)

        # 写入向量库以便语义搜索
        if self.embedding_adapter and self.vector_store:
            try:
                text_for_embedding = summary + " " + " ".join(key_facts)
                embedding = await self.embedding_adapter.embed([text_for_embedding], model=None)
                if embedding:
                    metadata = {
                        "conversation_id": conversation_id,
                        "key_facts": json.dumps(key_facts, ensure_ascii=False),
                        "timestamp": timestamp,
                        "tenant_id": self.tenant_id,
                    }
                    if user_id:
                        metadata["user_id"] = user_id
                    await self.vector_store.insert(
                        collection_name=self._collection_name,
                        ids=[episode_id],
                        contents=[text_for_embedding],
                        metadatas=[metadata],
                        embeddings=embedding,
                        dim=len(embedding[0]),
                    )
            except Exception:
                pass  # 向量写入失败不影响主流程

        return episode_id

    async def recall(self, query: str, user_id: str = "", top_k: int = 5) -> list[dict]:
        """基于语义相似度检索相关对话片段

        结果按 tenant_id 隔离，如果提供了 user_id 则进一步过滤。
        """
        if not self.embedding_adapter or not self.vector_store:
            return []

        try:
            query_embedding = await self.embedding_adapter.embed([query], model=None)
            if not query_embedding:
                return []

            results = await self.vector_store.search(
                collection_name=self._collection_name,
                query_embedding=query_embedding[0],
                top_k=top_k,
                dim=len(query_embedding[0]),
            )

            # Apply user_id metadata filter if provided
            episodes = []
            for r in results:
                meta = r.get("metadata", {})
                # Tenant isolation is handled by per-tenant collection name;
                # additionally filter by user_id when specified
                if user_id and meta.get("user_id", "") != user_id:
                    continue
                episode = {
                    "episode_id": r.get("id", ""),
                    "score": r.get("score", 0.0),
                    "summary": r.get("content", ""),
                    "conversation_id": meta.get("conversation_id", ""),
                    "key_facts": json.loads(meta.get("key_facts", "[]")),
                    "timestamp": meta.get("timestamp", 0),
                }
                episodes.append(episode)
            return episodes
        except Exception:
            return []


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """计算两个向量的余弦相似度"""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _extract_topics(text: str, top_n: int = 5) -> list[str]:
    """从文本中提取关键词/主题（基于词频 + 停用词过滤）"""
    tokens = _TOKEN_RE.findall(text.lower())
    # 过滤停用词和纯数字
    filtered = [
        t for t in tokens
        if t not in _STOPWORDS and not t.isdigit() and len(t) > 1
    ]
    if not filtered:
        return []

    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(top_n)]


class SummarizationPipeline:
    """短期记忆超限时自动摘要压缩管道"""

    def __init__(self, redis_client, llm_adapter=None, threshold: int = 20):
        self.redis = redis_client
        self.llm_adapter = llm_adapter
        self.threshold = threshold

    async def maybe_summarize(self, session_id: str, messages: list[dict]) -> Optional[str]:
        """当消息数超过阈值时，对较早的消息进行摘要压缩"""
        if len(messages) <= self.threshold:
            return None

        # 保留最近的消息，压缩更早的消息
        older = messages[self.threshold:]
        if not older:
            return None

        summary = await self._summarize_messages(older)
        if summary:
            key = f"memory:summary:{session_id}"
            await self.redis.set(key, summary, ex=86400 * 7)
        return summary

    async def _summarize_messages(self, messages: list[dict]) -> Optional[str]:
        """调用 LLM 对消息列表生成压缩摘要"""
        if not self.llm_adapter:
            # 无 LLM 时做简单拼接截断
            return self._fallback_summarize(messages)

        conversation = "\n".join(
            f"{m.get('role', 'unknown')}: {m.get('content', '')}"
            for m in messages
        )
        prompt = (
            "请将以下对话片段压缩为一段简洁的摘要，保留关键信息、决策和结论，"
            "控制在300字以内：\n\n"
            f"{conversation}"
        )
        try:
            response = await self.llm_adapter.chat(
                messages=[{"role": "user", "content": prompt}],
                model=None, temperature=0.1, max_tokens=400,
            )
            return response.content
        except Exception:
            return self._fallback_summarize(messages)

    def _fallback_summarize(self, messages: list[dict]) -> str:
        """无 LLM 时的降级方案：提取主题 + 截取首尾消息"""
        all_text = " ".join(m.get("content", "") for m in messages)
        topics = _extract_topics(all_text, top_n=3)

        first = messages[0].get("content", "")[:100] if messages else ""
        last = messages[-1].get("content", "")[:100] if messages else ""

        parts = []
        if topics:
            parts.append(f"主题: {', '.join(topics)}")
        if first:
            parts.append(f"开头: {first}")
        if last:
            parts.append(f"结尾: {last}")
        return " | ".join(parts)

    async def get_summary(self, session_id: str) -> str:
        key = f"memory:summary:{session_id}"
        data = await self.redis.get(key)
        return data if data else ""


class MemoryEngine:
    """Unified memory engine combining all tiers"""

    def __init__(
        self,
        redis_client,
        db_session=None,
        vector_store=None,
        embedding_adapter=None,
        llm_adapter=None,
        summarize_threshold: int = 20,
        tenant_id: str = "default",
    ):
        self.short_term = ShortTermMemory(redis_client)
        self.long_term = LongTermMemory(db_session, vector_store, embedding_adapter) if db_session and vector_store else None
        self.working = WorkingMemory(redis_client)
        self.episodic = EpisodicMemory(redis_client, embedding_adapter, vector_store, tenant_id=tenant_id)
        self.summarization = SummarizationPipeline(redis_client, llm_adapter, threshold=summarize_threshold)
        self.llm_adapter = llm_adapter

    async def add_message(self, session_id: str, tenant_id: str, user_id: str, role: str, content: str):
        await self.short_term.add_message(session_id, role, content)

        messages = await self.short_term.get_messages(session_id)
        if len(messages) >= 5 and self.long_term:
            await self.long_term.extract_and_store(session_id, tenant_id, user_id, messages, self.llm_adapter)

        if len(messages) >= 10:
            await self.working.compress(session_id, messages, self.llm_adapter)

        # 短期记忆超限时触发摘要压缩
        await self.summarization.maybe_summarize(session_id, messages)

    async def get_context(self, session_id: str, tenant_id: str, user_id: str, query: str = "") -> dict:
        short_term = await self.short_term.get_messages(session_id)
        working_summary = await self.working.get_summary(session_id)
        relevant = []

        if self.long_term and query:
            relevant = await self.long_term.search(query, tenant_id, user_id)

        # 获取摘要压缩结果
        summarized = await self.summarization.get_summary(session_id)

        # 提取主题（基于当前查询和短期记忆）
        all_text = " ".join(m.get("content", "") for m in short_term)
        if query:
            all_text += " " + query
        topics = _extract_topics(all_text) if all_text else []

        return {
            "short_term": short_term,
            "working_summary": working_summary,
            "relevant_memories": relevant,
            "summarized_older": summarized,
            "topics": topics,
        }

    async def clear_session(self, session_id: str):
        await self.short_term.clear(session_id)
