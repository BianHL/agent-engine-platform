"""Document chunking strategies: recursive, semantic, parent-child, Q&A pair.

Parent-child chunking creates large parent chunks for context and small child
chunks for retrieval.  Child chunks carry ``parent_id`` metadata so that
matched children can be promoted back to their full parent context.
"""

from __future__ import annotations

import uuid
from typing import Optional

# Rough approximation: 1 Chinese character ~ 1 token, 1 English word ~ 1.3 tokens.
# Using a conservative average of ~1.5 chars per token for mixed content.
_CHARS_PER_TOKEN = 1.5


class DocumentChunker:
    """General-purpose document chunker with multiple strategies.

    Parameters
    ----------
    chunk_size : int
        Maximum characters per chunk for recursive / semantic strategies.
    chunk_overlap : int
        Number of overlapping characters between consecutive chunks.
    """

    # Defaults for parent-child mode (in approximate tokens)
    PARENT_TOKEN_SIZE = 1024
    CHILD_TOKEN_SIZE = 256

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, strategy: str = "recursive") -> list[dict]:
        if strategy == "semantic":
            return self._semantic_chunk(text)
        elif strategy == "parent_child":
            return self._parent_child_chunk(text)
        elif strategy == "qa_pair":
            return self._qa_pair_chunk(text)
        return self._recursive_chunk(text)

    # ------------------------------------------------------------------
    # Recursive chunking
    # ------------------------------------------------------------------

    def _recursive_chunk(self, text: str) -> list[dict]:
        chunks = []
        separators = ["\n\n", "\n", "。", ".", "！", "!", "？", "?", "；", ";"]
        current_text = text

        while current_text:
            if len(current_text) <= self.chunk_size:
                chunk_text = current_text.strip()
                if chunk_text:
                    chunks.append(
                        {
                            "content": chunk_text,
                            "index": len(chunks),
                            "start": 0,
                            "end": len(chunk_text),
                        }
                    )
                break

            split_pos = -1
            for sep in separators:
                pos = current_text.rfind(sep, 0, self.chunk_size)
                if pos > 0:
                    split_pos = pos + len(sep)
                    break

            if split_pos <= 0:
                split_pos = self.chunk_size

            chunk_text = current_text[:split_pos].strip()
            if chunk_text:
                chunks.append(
                    {
                        "content": chunk_text,
                        "index": len(chunks),
                        "start": 0,
                        "end": split_pos,
                    }
                )

            overlap_start = max(0, split_pos - self.chunk_overlap)
            current_text = current_text[overlap_start:]

        return chunks

    # ------------------------------------------------------------------
    # Semantic chunking
    # ------------------------------------------------------------------

    def _semantic_chunk(self, text: str) -> list[dict]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "index": len(chunks),
                        "start": 0,
                        "end": len(current_chunk),
                    }
                )
                words = current_chunk.split()
                overlap_text = (
                    " ".join(words[-self.chunk_overlap:])
                    if len(words) > self.chunk_overlap
                    else ""
                )
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para

        if current_chunk.strip():
            chunks.append(
                {
                    "content": current_chunk.strip(),
                    "index": len(chunks),
                    "start": 0,
                    "end": len(current_chunk),
                }
            )

        return chunks

    # ------------------------------------------------------------------
    # Parent-child chunking
    # ------------------------------------------------------------------

    def _parent_child_chunk(self, text: str) -> list[dict]:
        """Split text into large parent chunks, then split each parent into
        smaller child chunks.  Each child carries its ``parent_id`` so retrieval
        can promote matched children back to the full parent context.

        Returns a flat list containing both parent and child chunk dicts.
        """
        parent_size = self._tokens_to_chars(self.PARENT_TOKEN_SIZE)
        child_size = self._tokens_to_chars(self.CHILD_TOKEN_SIZE)
        child_overlap = max(10, child_size // 5)

        # Step 1: create parent chunks
        parent_chunks = self._split_into_chunks(text, parent_size, self.chunk_overlap)

        all_chunks: list[dict] = []
        for p_idx, parent in enumerate(parent_chunks):
            parent_id = str(uuid.uuid4())
            parent_content = parent["content"]
            parent_chunk = {
                "content": parent_content,
                "index": p_idx,
                "start": parent["start"],
                "end": parent["end"],
                "chunk_type": "parent",
                "parent_id": None,
                "chunk_id": parent_id,
            }
            all_chunks.append(parent_chunk)

            # Step 2: split each parent into child chunks
            child_chunks = self._split_into_chunks(
                parent_content, child_size, child_overlap,
            )
            for c_idx, child in enumerate(child_chunks):
                child_chunk = {
                    "content": child["content"],
                    "index": c_idx,
                    "start": parent["start"] + child["start"],
                    "end": parent["start"] + child["end"],
                    "chunk_type": "child",
                    "parent_id": parent_id,
                    "chunk_id": str(uuid.uuid4()),
                }
                all_chunks.append(child_chunk)

        return all_chunks

    # ------------------------------------------------------------------
    # Q&A pair extraction
    # ------------------------------------------------------------------

    def _qa_pair_chunk(self, text: str) -> list[dict]:
        """Heuristic Q&A pair extraction without LLM."""
        chunks: list[dict] = []
        lines = text.split("\n")

        current_question: Optional[str] = None
        current_answer_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_answer_lines:
                    current_answer_lines.append("")
                continue

            is_question = False
            question_text = stripped

            if stripped.upper().startswith("Q:") or stripped.upper().startswith("Q："):
                question_text = stripped[2:].strip()
                is_question = True
            elif stripped.upper().startswith("问:") or stripped.startswith("问："):
                question_text = stripped[2:].strip()
                is_question = True
            elif stripped.endswith("?") or stripped.endswith("？"):
                is_question = True

            if is_question:
                if current_question and current_answer_lines:
                    answer_text = "\n".join(current_answer_lines).strip()
                    if answer_text:
                        chunks.append(self._make_qa_chunk(
                            current_question, answer_text, len(chunks),
                        ))
                current_question = question_text
                current_answer_lines = []
                continue

            if stripped.upper().startswith("A:") or stripped.upper().startswith("A："):
                current_answer_lines.append(stripped[2:].strip())
            elif stripped.startswith("答:") or stripped.startswith("答："):
                current_answer_lines.append(stripped[2:].strip())
            elif current_question is not None:
                current_answer_lines.append(stripped)

        if current_question and current_answer_lines:
            answer_text = "\n".join(current_answer_lines).strip()
            if answer_text:
                chunks.append(self._make_qa_chunk(
                    current_question, answer_text, len(chunks),
                ))

        if not chunks:
            return self._recursive_chunk(text)

        return chunks

    @staticmethod
    def _make_qa_chunk(question: str, answer: str, index: int) -> dict:
        return {
            "content": f"问题：{question}\n回答：{answer}",
            "index": index,
            "start": 0,
            "end": len(question) + len(answer),
            "chunk_type": "qa_pair",
            "question": question,
            "answer": answer,
            "chunk_id": str(uuid.uuid4()),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _split_into_chunks(
        self, text: str, size: int, overlap: int,
    ) -> list[dict]:
        """Generic helper: split text into chunks with overlap."""
        chunks: list[dict] = []
        separators = ["\n\n", "\n", "。", ".", "！", "!", "？", "?", "；", ";"]
        current_text = text
        offset = 0

        while current_text:
            if len(current_text) <= size:
                chunk_text = current_text.strip()
                if chunk_text:
                    chunks.append({
                        "content": chunk_text,
                        "index": len(chunks),
                        "start": offset,
                        "end": offset + len(current_text),
                    })
                break

            split_pos = -1
            for sep in separators:
                pos = current_text.rfind(sep, 0, size)
                if pos > 0:
                    split_pos = pos + len(sep)
                    break
            if split_pos <= 0:
                split_pos = size

            chunk_text = current_text[:split_pos].strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "index": len(chunks),
                    "start": offset,
                    "end": offset + split_pos,
                })

            overlap_start = max(0, split_pos - overlap)
            advance = split_pos - overlap_start
            offset += advance
            current_text = current_text[overlap_start:]

        return chunks

    async def qa_pair_chunk_async(
        self, text: str, llm_adapter=None,
    ) -> list[dict]:
        """LLM-powered Q&A pair extraction for higher-quality results."""
        if not llm_adapter:
            return self._qa_pair_chunk(text)

        prompt = (
            "请从以下文档中提取问答对。每对占一行，格式为："
            "Q: <问题> | A: <回答>\n"
            "如果没有明确的问答内容，请根据文档内容生成3-5个可能的问答对。\n\n"
            f"文档内容：\n{text[:4000]}"
        )

        try:
            response = await llm_adapter.chat(
                messages=[{"role": "user", "content": prompt}],
                model=None,
                temperature=0.3,
                max_tokens=2000,
            )
            qa_text = response.content
            return self._qa_pair_chunk(qa_text)
        except Exception:
            return self._qa_pair_chunk(text)

    @staticmethod
    def _tokens_to_chars(tokens: int) -> int:
        """Convert an approximate token count to a character count."""
        return int(tokens * _CHARS_PER_TOKEN)


class ParentChildChunker:
    """Dedicated parent-child chunker with configurable token sizes.

    Creates large parent chunks for context and small child chunks for
    retrieval.  Child chunks carry ``parent_id`` so retrieval can promote
    matched children to their full parent context.

    Parameters
    ----------
    parent_token_size : int
        Target size of parent chunks in approximate tokens (default 1024).
    child_token_size : int
        Target size of child chunks in approximate tokens (default 256).
    chunk_overlap : int
        Character overlap between consecutive chunks within a parent.
    """

    def __init__(
        self,
        parent_token_size: int = 1024,
        child_token_size: int = 256,
        chunk_overlap: int = 50,
    ):
        self.parent_token_size = parent_token_size
        self.child_token_size = child_token_size
        self.chunk_overlap = chunk_overlap
        self._inner = DocumentChunker(
            chunk_size=DocumentChunker._tokens_to_chars(child_token_size),
            chunk_overlap=chunk_overlap,
        )

    def chunk(self, text: str) -> list[dict]:
        """Split text into parent-child chunk pairs.

        Returns a flat list of chunk dicts.  Parent chunks have
        ``chunk_type == "parent"`` and ``parent_id is None``.  Child chunks
        have ``chunk_type == "child"`` and carry their ``parent_id``.
        """
        parent_size = DocumentChunker._tokens_to_chars(self.parent_token_size)
        child_size = DocumentChunker._tokens_to_chars(self.child_token_size)
        child_overlap = max(10, child_size // 5)

        # Step 1: create parent chunks
        parent_chunks = self._inner._split_into_chunks(
            text, parent_size, self.chunk_overlap,
        )

        all_chunks: list[dict] = []
        for p_idx, parent in enumerate(parent_chunks):
            parent_id = str(uuid.uuid4())
            parent_content = parent["content"]

            all_chunks.append({
                "content": parent_content,
                "index": p_idx,
                "start": parent["start"],
                "end": parent["end"],
                "chunk_type": "parent",
                "parent_id": None,
                "chunk_id": parent_id,
                "token_size": self.parent_token_size,
            })

            # Step 2: split each parent into child chunks
            children = self._inner._split_into_chunks(
                parent_content, child_size, child_overlap,
            )
            for c_idx, child in enumerate(children):
                all_chunks.append({
                    "content": child["content"],
                    "index": c_idx,
                    "start": parent["start"] + child["start"],
                    "end": parent["start"] + child["end"],
                    "chunk_type": "child",
                    "parent_id": parent_id,
                    "chunk_id": str(uuid.uuid4()),
                    "token_size": self.child_token_size,
                })

        return all_chunks

    @staticmethod
    def get_parent_context(
        chunks: list[dict], child_chunk_id: str,
    ) -> Optional[dict]:
        """Given a child chunk's ID, find and return its parent chunk.

        Useful during retrieval: return the child's match but use the
        parent for expanded context.
        """
        # Build a lookup of parent_id -> parent chunk
        parent_map: dict[str, dict] = {}
        child_parent_id: Optional[str] = None

        for chunk in chunks:
            if chunk.get("chunk_type") == "parent":
                parent_map[chunk["chunk_id"]] = chunk
            if (
                chunk.get("chunk_id") == child_chunk_id
                and chunk.get("parent_id")
            ):
                child_parent_id = chunk["parent_id"]

        if child_parent_id and child_parent_id in parent_map:
            return parent_map[child_parent_id]
        return None
