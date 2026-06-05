"""Ragas-style evaluation engine with 5 core metrics.

Metrics:
- faithfulness: does answer stay grounded in retrieved context?
- answer_relevancy: is answer relevant to question?
- context_precision: are retrieved contexts in good order?
- context_recall: does retrieval cover all needed info?
- tool_call_accuracy: were tool calls correct?
"""
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM adapter protocol (matches BaseLLMAdapter.chat signature)
# ---------------------------------------------------------------------------

class LLMAdapter(Protocol):
    """Minimal interface for LLM calls used by evaluation metrics."""

    async def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> Any: ...


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _extract_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in parts if s.strip()]


def _normalize(text: str) -> str:
    """Normalize text for comparison."""
    return re.sub(r'\s+', ' ', text.strip().lower())


# ---------------------------------------------------------------------------
# Core Metrics
# ---------------------------------------------------------------------------

async def faithfulness(answer: str, contexts: list[str], llm: Optional[LLMAdapter] = None, model: str = "") -> float:
    """Check if claims in answer are supported by context sentences.

    Returns a score between 0 and 1.
    """
    if not answer or not contexts:
        return 0.0

    claims = _extract_sentences(answer)
    if not claims:
        return 0.0

    context_text = "\n".join(contexts)

    if llm and model:
        prompt = (
            "Given the following context, determine which of the claims are supported.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Claims:\n" + "\n".join(f"{i+1}. {c}" for i, c in enumerate(claims)) + "\n\n"
            'Return JSON: {"supported": [list of supported claim numbers]}'
        )
        messages = [{"role": "user", "content": prompt}]
        resp = await llm.chat(messages=messages, model=model, temperature=0.0, max_tokens=512)
        try:
            content = resp.content if hasattr(resp, "content") else str(resp)
            data = json.loads(content)
            supported = len(data.get("supported", []))
            return min(supported / len(claims), 1.0)
        except (json.JSONDecodeError, AttributeError, ZeroDivisionError) as e:
            logger.debug("LLM faithfulness parse failed, falling back to heuristic: %s", e)

    # Fallback: simple keyword overlap heuristic
    supported = 0
    context_lower = _normalize(context_text)
    for claim in claims:
        words = set(_normalize(claim).split())
        words = {w for w in words if len(w) > 3}
        if words and any(w in context_lower for w in words):
            supported += 1
    return supported / len(claims) if claims else 0.0


async def answer_relevancy(answer: str, question: str, llm: Optional[LLMAdapter] = None, model: str = "") -> float:
    """Check if answer is relevant to question. Score 0-1."""
    if not answer or not question:
        return 0.0

    if llm and model:
        prompt = (
            "Rate how relevant the answer is to the question on a scale of 0 to 1.\n"
            'Return JSON: {"score": <float between 0 and 1>}\n\n'
            f"Question: {question}\nAnswer: {answer}"
        )
        messages = [{"role": "user", "content": prompt}]
        resp = await llm.chat(messages=messages, model=model, temperature=0.0, max_tokens=256)
        try:
            content = resp.content if hasattr(resp, "content") else str(resp)
            data = json.loads(content)
            score = float(data.get("score", 0.0))
            return max(0.0, min(score, 1.0))
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            logger.debug("LLM answer_relevancy parse failed, falling back to heuristic: %s", e)

    # Fallback: keyword overlap
    q_words = set(_normalize(question).split())
    a_words = set(_normalize(answer).split())
    q_words = {w for w in q_words if len(w) > 3}
    a_words = {w for w in a_words if len(w) > 3}
    if not q_words:
        return 0.0
    overlap = len(q_words & a_words)
    return min(overlap / len(q_words), 1.0)


async def context_precision(
    contexts: list[str],
    ground_truth: str,
    llm: Optional[LLMAdapter] = None,
    model: str = "",
) -> float:
    """Check if relevant contexts rank higher. Score 0-1."""
    if not contexts or not ground_truth:
        return 0.0

    if llm and model:
        ctx_list = "\n".join(f"[{i}] {c}" for i, c in enumerate(contexts))
        prompt = (
            "Given the ground truth, rate each context's relevance (0 or 1) and "
            "calculate precision@k for the ranking order.\n"
            'Return JSON: {"relevance": [0/1 per context in order], "precision": <float>}\n\n'
            f"Ground truth: {ground_truth}\nContexts:\n{ctx_list}"
        )
        messages = [{"role": "user", "content": prompt}]
        resp = await llm.chat(messages=messages, model=model, temperature=0.0, max_tokens=512)
        try:
            content = resp.content if hasattr(resp, "content") else str(resp)
            data = json.loads(content)
            return float(data.get("precision", 0.0))
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            logger.debug("LLM context_precision parse failed, falling back to heuristic: %s", e)

    # Fallback: check if contexts with keyword overlap appear earlier
    gt_lower = _normalize(ground_truth)
    gt_words = {w for w in gt_lower.split() if len(w) > 3}
    relevant_positions = []
    for i, ctx in enumerate(contexts):
        ctx_words = set(_normalize(ctx).split())
        if gt_words & ctx_words:
            relevant_positions.append(i)

    if not relevant_positions:
        return 0.0

    # Average precision: relevant docs earlier = better
    n = len(contexts)
    precision_sum = 0.0
    for rank, pos in enumerate(relevant_positions):
        precision_sum += (rank + 1) / (pos + 1)
    return precision_sum / len(relevant_positions) if relevant_positions else 0.0


async def context_recall(
    contexts: list[str],
    ground_truth: str,
    llm: Optional[LLMAdapter] = None,
    model: str = "",
) -> float:
    """Check coverage of ground truth statements. Score 0-1."""
    if not contexts or not ground_truth:
        return 0.0

    gt_statements = _extract_sentences(ground_truth)
    if not gt_statements:
        return 0.0

    context_text = "\n".join(contexts)

    if llm and model:
        prompt = (
            "Given the contexts, determine which ground truth statements are covered.\n\n"
            f"Contexts:\n{context_text}\n\n"
            f"Ground truth statements:\n"
            + "\n".join(f"{i+1}. {s}" for i, s in enumerate(gt_statements))
            + '\n\nReturn JSON: {"covered": [list of covered statement numbers]}'
        )
        messages = [{"role": "user", "content": prompt}]
        resp = await llm.chat(messages=messages, model=model, temperature=0.0, max_tokens=512)
        try:
            content = resp.content if hasattr(resp, "content") else str(resp)
            data = json.loads(content)
            covered = len(data.get("covered", []))
            return min(covered / len(gt_statements), 1.0)
        except (json.JSONDecodeError, AttributeError, ZeroDivisionError) as e:
            logger.debug("LLM context_recall parse failed, falling back to heuristic: %s", e)

    # Fallback: keyword overlap per statement
    context_lower = _normalize(context_text)
    covered = 0
    for stmt in gt_statements:
        words = {w for w in _normalize(stmt).split() if len(w) > 3}
        if words and any(w in context_lower for w in words):
            covered += 1
    return covered / len(gt_statements)


async def tool_call_accuracy(
    tool_calls: list[dict],
    expected_calls: list[dict],
    llm: Optional[LLMAdapter] = None,
    model: str = "",
) -> float:
    """Compare function names and arguments. Score 0-1."""
    if not expected_calls:
        return 1.0 if not tool_calls else 0.0
    if not tool_calls:
        return 0.0

    if llm and model:
        prompt = (
            "Compare the actual tool calls with expected tool calls.\n"
            'Return JSON: {"score": <float 0-1>, "matched": [indices of matched expected calls]}\n\n'
            f"Expected: {json.dumps(expected_calls)}\n"
            f"Actual: {json.dumps(tool_calls)}"
        )
        messages = [{"role": "user", "content": prompt}]
        resp = await llm.chat(messages=messages, model=model, temperature=0.0, max_tokens=512)
        try:
            content = resp.content if hasattr(resp, "content") else str(resp)
            data = json.loads(content)
            return float(data.get("score", 0.0))
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            logger.debug("LLM tool_call_accuracy parse failed, falling back to heuristic: %s", e)

    # Fallback: exact match on function name + args
    matched = 0
    for expected in expected_calls:
        exp_name = expected.get("name", "")
        exp_args = expected.get("arguments", {})
        for actual in tool_calls:
            act_name = actual.get("name", "")
            act_args = actual.get("arguments", {})
            if act_name == exp_name and act_args == exp_args:
                matched += 1
                break
    return matched / len(expected_calls)


# ---------------------------------------------------------------------------
# Main evaluation engine
# ---------------------------------------------------------------------------

METRIC_REGISTRY = {
    "faithfulness": faithfulness,
    "answer_relevancy": answer_relevancy,
    "context_precision": context_precision,
    "context_recall": context_recall,
    "tool_call_accuracy": tool_call_accuracy,
}


@dataclass
class EvalResult:
    """Result for a single test case."""
    test_case_index: int
    input_text: str
    expected_output: str
    actual_output: str
    scores: dict[str, float]
    latency_ms: int = 0


@dataclass
class EvalSummary:
    """Aggregated results for an evaluation run."""
    results: list[EvalResult] = field(default_factory=list)
    metric_averages: dict[str, float] = field(default_factory=dict)

    def compute_averages(self) -> None:
        metric_sums: dict[str, float] = {}
        metric_counts: dict[str, int] = {}
        for r in self.results:
            for metric, score in r.scores.items():
                metric_sums[metric] = metric_sums.get(metric, 0.0) + score
                metric_counts[metric] = metric_counts.get(metric, 0) + 1
        self.metric_averages = {
            m: metric_sums[m] / metric_counts[m]
            for m in metric_sums
            if metric_counts[m] > 0
        }


class EvaluationEngine:
    """Run Ragas-style evaluations on agent outputs."""

    def __init__(self, llm_adapter: Optional[LLMAdapter] = None, model: str = ""):
        self.llm = llm_adapter
        self.model = model

    async def run_metric(
        self,
        metric_name: str,
        test_case: dict[str, Any],
    ) -> float:
        """Run a single metric on a single test case."""
        func = METRIC_REGISTRY.get(metric_name)
        if not func:
            raise ValueError(f"Unknown metric: {metric_name}")

        kwargs: dict[str, Any] = {}
        if metric_name == "faithfulness":
            kwargs = {"answer": test_case.get("answer", ""), "contexts": test_case.get("contexts", [])}
        elif metric_name == "answer_relevancy":
            kwargs = {"answer": test_case.get("answer", ""), "question": test_case.get("question", "")}
        elif metric_name in ("context_precision", "context_recall"):
            kwargs = {"contexts": test_case.get("contexts", []), "ground_truth": test_case.get("ground_truth", "")}
        elif metric_name == "tool_call_accuracy":
            kwargs = {"tool_calls": test_case.get("tool_calls", []), "expected_calls": test_case.get("expected_tool_calls", [])}

        if self.llm and self.model:
            kwargs["llm"] = self.llm
            kwargs["model"] = self.model

        return await func(**kwargs)

    async def evaluate(
        self,
        dataset: list[dict[str, Any]],
        metrics: list[str],
    ) -> EvalSummary:
        """Run all specified metrics on the full dataset."""
        # Validate metrics
        for m in metrics:
            if m not in METRIC_REGISTRY:
                raise ValueError(f"Unknown metric: {m}. Available: {list(METRIC_REGISTRY)}")

        summary = EvalSummary()
        for idx, test_case in enumerate(dataset):
            scores: dict[str, float] = {}
            for metric_name in metrics:
                scores[metric_name] = await self.run_metric(metric_name, test_case)

            summary.results.append(EvalResult(
                test_case_index=idx,
                input_text=test_case.get("question", ""),
                expected_output=test_case.get("ground_truth", ""),
                actual_output=test_case.get("answer", ""),
                scores=scores,
            ))

        summary.compute_averages()
        return summary
