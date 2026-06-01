"""Dataset loading, extraction, and export for evaluation."""
import csv
import json
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import ConversationModel, MessageModel


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def load_dataset(file_path: str) -> list[dict[str, Any]]:
    """Load evaluation dataset from JSON or CSV file.

    Expected format (JSON):
    [
      {"question": "...", "contexts": [...], "answer": "...", "ground_truth": "...",
       "tool_calls": [...], "expected_tool_calls": [...]}
    ]
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON dataset must be a list of test cases")
        return _validate_dataset(data)

    if suffix == ".csv":
        return _load_csv(path)

    raise ValueError(f"Unsupported file format: {suffix}. Use .json or .csv")


def _load_csv(path: Path) -> list[dict[str, Any]]:
    """Load dataset from CSV file."""
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case: dict[str, Any] = {}
            case["question"] = row.get("question", "")
            case["answer"] = row.get("answer", "")
            case["ground_truth"] = row.get("ground_truth", "")

            # Parse contexts (semicolon-separated or JSON)
            raw_ctx = row.get("contexts", "")
            if raw_ctx.startswith("["):
                case["contexts"] = json.loads(raw_ctx)
            else:
                case["contexts"] = [c.strip() for c in raw_ctx.split(";") if c.strip()]

            # Parse tool calls if present
            tc = row.get("tool_calls", "")
            case["tool_calls"] = json.loads(tc) if tc else []
            etc = row.get("expected_tool_calls", "")
            case["expected_tool_calls"] = json.loads(etc) if etc else []

            rows.append(case)
    return _validate_dataset(rows)


def _validate_dataset(data: list[dict]) -> list[dict[str, Any]]:
    """Validate and normalize dataset entries."""
    validated: list[dict[str, Any]] = []
    for i, item in enumerate(data):
        case: dict[str, Any] = {
            "question": str(item.get("question", "")),
            "answer": str(item.get("answer", "")),
            "ground_truth": str(item.get("ground_truth", "")),
            "contexts": item.get("contexts", []),
            "tool_calls": item.get("tool_calls", []),
            "expected_tool_calls": item.get("expected_tool_calls", []),
        }
        if not isinstance(case["contexts"], list):
            case["contexts"] = [str(case["contexts"])]
        validated.append(case)
    return validated


def export_dataset(data: list[dict[str, Any]], file_path: str) -> None:
    """Export dataset to JSON or CSV file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    suffix = path.suffix.lower()
    if suffix == ".json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    elif suffix == ".csv":
        if not data:
            return
        fieldnames = ["question", "answer", "ground_truth", "contexts", "tool_calls", "expected_tool_calls"]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                csv_row = dict(row)
                csv_row["contexts"] = json.dumps(csv_row.get("contexts", []), ensure_ascii=False)
                csv_row["tool_calls"] = json.dumps(csv_row.get("tool_calls", []), ensure_ascii=False)
                csv_row["expected_tool_calls"] = json.dumps(csv_row.get("expected_tool_calls", []), ensure_ascii=False)
                writer.writerow(csv_row)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


# ---------------------------------------------------------------------------
# Extract from conversation logs
# ---------------------------------------------------------------------------

async def extract_from_logs(
    db: AsyncSession,
    agent_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Extract evaluation data from production conversation logs.

    For each conversation with the agent, pairs user messages (question)
    with the next assistant message (answer).
    """
    # Get conversations for this agent
    stmt = (
        select(ConversationModel)
        .where(ConversationModel.agent_id == agent_id)
        .order_by(ConversationModel.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()

    dataset: list[dict[str, Any]] = []

    for conv in conversations:
        # Get messages in order
        msg_stmt = (
            select(MessageModel)
            .where(MessageModel.conversation_id == conv.id)
            .order_by(MessageModel.created_at.asc())
        )
        msg_result = await db.execute(msg_stmt)
        messages = msg_result.scalars().all()

        # Pair user/assistant messages
        pending_question: Optional[str] = None
        for msg in messages:
            if msg.role == "user":
                pending_question = msg.content
            elif msg.role == "assistant" and pending_question:
                # Extract retrieval contexts from metadata if available
                meta = msg.meta_info or {}
                contexts = meta.get("contexts", [])
                if isinstance(contexts, list) and contexts:
                    if isinstance(contexts[0], dict):
                        contexts = [c.get("content", str(c)) for c in contexts]

                dataset.append({
                    "question": pending_question,
                    "answer": msg.content,
                    "ground_truth": "",  # no ground truth in production logs
                    "contexts": contexts,
                    "tool_calls": meta.get("tool_calls", []),
                    "expected_tool_calls": [],
                })
                pending_question = None

    return dataset
