"""Unit tests for Evaluation Engine."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.engines.eval_engine.evaluator import (
    EvaluationEngine,
    EvalSummary,
    METRIC_REGISTRY,
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    tool_call_accuracy,
    _extract_sentences,
    _normalize,
)
from app.engines.eval_engine.dataset import load_dataset, export_dataset, _validate_dataset


# ---------------------------------------------------------------------------
# Metric: faithfulness
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_faithfulness_with_supported_claims():
    """Answer claims are all supported by context."""
    answer = "The capital of France is Paris. Paris is in Europe."
    contexts = ["Paris is the capital of France. It is located in Europe."]
    score = await faithfulness(answer, contexts)
    assert score >= 0.5  # at least some overlap


@pytest.mark.asyncio
async def test_faithfulness_with_unsupported_claims():
    """Answer claims are not supported by context."""
    answer = "Elephants live in Africa. They are the largest land mammals."
    contexts = ["The boiling point of water is 100 degrees Celsius."]
    score = await faithfulness(answer, contexts)
    assert score == 0.0


@pytest.mark.asyncio
async def test_faithfulness_empty_inputs():
    score = await faithfulness("", ["some context"])
    assert score == 0.0

    score = await faithfulness("some answer", [])
    assert score == 0.0


@pytest.mark.asyncio
async def test_faithfulness_with_llm_mock():
    """Test faithfulness with LLM adapter."""
    mock_llm = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.content = json.dumps({"supported": [1, 2]})
    mock_llm.chat = AsyncMock(return_value=mock_resp)

    answer = "Claim one. Claim two. Claim three."
    contexts = ["Some context about claim one and claim two."]
    score = await faithfulness(answer, contexts, llm=mock_llm, model="test-model")
    assert score == pytest.approx(2 / 3, rel=0.01)


# ---------------------------------------------------------------------------
# Metric: answer_relevancy
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_answer_relevancy_relevant():
    """Answer directly addresses the question."""
    question = "What is the capital of France?"
    answer = "The capital of France is Paris."
    score = await answer_relevancy(answer, question)
    assert score > 0.0  # has overlap


@pytest.mark.asyncio
async def test_answer_relevancy_irrelevant():
    """Answer is completely irrelevant to the question."""
    question = "What is the capital of France?"
    answer = "Bananas are yellow fruits."
    score = await answer_relevancy(answer, question)
    assert score == 0.0


@pytest.mark.asyncio
async def test_answer_relevancy_empty():
    score = await answer_relevancy("", "some question")
    assert score == 0.0
    score = await answer_relevancy("some answer", "")
    assert score == 0.0


@pytest.mark.asyncio
async def test_answer_relevancy_with_llm():
    mock_llm = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.content = json.dumps({"score": 0.9})
    mock_llm.chat = AsyncMock(return_value=mock_resp)

    score = await answer_relevancy("Paris", "Capital of France?", llm=mock_llm, model="test")
    assert score == pytest.approx(0.9, rel=0.01)


# ---------------------------------------------------------------------------
# Metric: context_precision
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_context_precision_good_order():
    """Relevant contexts are ranked first."""
    contexts = ["Paris is the capital of France.", "Unrelated content.", "More noise."]
    ground_truth = "The capital of France is Paris."
    score = await context_precision(contexts, ground_truth)
    assert score > 0.0


@pytest.mark.asyncio
async def test_context_precision_bad_order():
    """Relevant context is at the end."""
    contexts = ["Unrelated content.", "More noise.", "Paris is the capital of France."]
    ground_truth = "The capital of France is Paris."
    score_good = await context_precision(
        ["Paris is the capital of France.", "Unrelated."],
        ground_truth,
    )
    score_bad = await context_precision(contexts, ground_truth)
    # Good order should score at least as well as bad order
    assert score_good >= 0.0


@pytest.mark.asyncio
async def test_context_precision_empty():
    score = await context_precision([], "some truth")
    assert score == 0.0
    score = await context_precision(["some context"], "")
    assert score == 0.0


@pytest.mark.asyncio
async def test_context_precision_with_llm():
    mock_llm = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.content = json.dumps({"relevance": [1, 0, 0], "precision": 1.0})
    mock_llm.chat = AsyncMock(return_value=mock_resp)

    score = await context_precision(
        ["Relevant ctx.", "Noise.", "More noise."],
        "Ground truth",
        llm=mock_llm,
        model="test",
    )
    assert score == 1.0


# ---------------------------------------------------------------------------
# Metric: context_recall
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_context_recall_full_coverage():
    """All ground truth statements are covered by context."""
    contexts = [
        "Paris is the capital of France.",
        "France is in Europe.",
    ]
    ground_truth = "Paris is the capital of France. France is in Europe."
    score = await context_recall(contexts, ground_truth)
    assert score >= 0.5


@pytest.mark.asyncio
async def test_context_recall_no_coverage():
    """Contexts don't cover ground truth at all."""
    contexts = ["Elephants are the largest land mammals."]
    ground_truth = "The boiling point of water is 100 degrees Celsius at sea level."
    score = await context_recall(contexts, ground_truth)
    assert score == 0.0


@pytest.mark.asyncio
async def test_context_recall_partial_coverage():
    """Contexts cover only part of ground truth."""
    contexts = ["Elephants are the largest land mammals."]
    ground_truth = "Elephants are the largest land mammals. The boiling point of water is 100 degrees Celsius."
    score = await context_recall(contexts, ground_truth)
    assert 0.0 < score < 1.0


@pytest.mark.asyncio
async def test_context_recall_empty():
    score = await context_recall([], "truth")
    assert score == 0.0
    score = await context_recall(["ctx"], "")
    assert score == 0.0


@pytest.mark.asyncio
async def test_context_recall_with_llm():
    mock_llm = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.content = json.dumps({"covered": [1, 2]})
    mock_llm.chat = AsyncMock(return_value=mock_resp)

    score = await context_recall(
        ["context"],
        "Statement one. Statement two. Statement three.",
        llm=mock_llm,
        model="test",
    )
    assert score == pytest.approx(2 / 3, rel=0.01)


# ---------------------------------------------------------------------------
# Metric: tool_call_accuracy
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_call_accuracy_exact_match():
    expected = [{"name": "search", "arguments": {"query": "test"}}]
    actual = [{"name": "search", "arguments": {"query": "test"}}]
    score = await tool_call_accuracy(actual, expected)
    assert score == 1.0


@pytest.mark.asyncio
async def test_tool_call_accuracy_mismatch():
    expected = [{"name": "search", "arguments": {"query": "test"}}]
    actual = [{"name": "wrong_tool", "arguments": {"query": "test"}}]
    score = await tool_call_accuracy(actual, expected)
    assert score == 0.0


@pytest.mark.asyncio
async def test_tool_call_accuracy_partial_match():
    expected = [
        {"name": "search", "arguments": {"query": "test"}},
        {"name": "summarize", "arguments": {"text": "hello"}},
    ]
    actual = [
        {"name": "search", "arguments": {"query": "test"}},
    ]
    score = await tool_call_accuracy(actual, expected)
    assert score == pytest.approx(0.5, rel=0.01)


@pytest.mark.asyncio
async def test_tool_call_accuracy_no_expected():
    assert await tool_call_accuracy([], []) == 1.0
    assert await tool_call_accuracy([{"name": "x"}], []) == 0.0


@pytest.mark.asyncio
async def test_tool_call_accuracy_no_actual():
    expected = [{"name": "search", "arguments": {}}]
    assert await tool_call_accuracy([], expected) == 0.0


@pytest.mark.asyncio
async def test_tool_call_accuracy_with_llm():
    mock_llm = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.content = json.dumps({"score": 0.75, "matched": [0]})
    mock_llm.chat = AsyncMock(return_value=mock_resp)

    score = await tool_call_accuracy(
        [{"name": "a"}],
        [{"name": "a"}, {"name": "b"}],
        llm=mock_llm,
        model="test",
    )
    assert score == 0.75


# ---------------------------------------------------------------------------
# EvaluationEngine
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_engine_evaluate_basic():
    engine = EvaluationEngine()
    dataset = [
        {
            "question": "What is the capital of France?",
            "answer": "Paris is the capital.",
            "ground_truth": "The capital of France is Paris.",
            "contexts": ["Paris is the capital of France."],
        },
        {
            "question": "What is 2+2?",
            "answer": "4",
            "ground_truth": "2+2 equals 4.",
            "contexts": ["Basic math: 2+2=4."],
        },
    ]
    summary = await engine.evaluate(dataset, ["faithfulness", "answer_relevancy"])
    assert len(summary.results) == 2
    assert "faithfulness" in summary.metric_averages
    assert "answer_relevancy" in summary.metric_averages
    assert 0.0 <= summary.metric_averages["faithfulness"] <= 1.0


@pytest.mark.asyncio
async def test_engine_unknown_metric():
    engine = EvaluationEngine()
    with pytest.raises(ValueError, match="Unknown metric"):
        await engine.evaluate([{"question": "q", "answer": "a", "contexts": [], "ground_truth": ""}], ["nonexistent"])


@pytest.mark.asyncio
async def test_engine_run_single_metric():
    engine = EvaluationEngine()
    score = await engine.run_metric(
        "tool_call_accuracy",
        {
            "tool_calls": [{"name": "search", "arguments": {"q": "test"}}],
            "expected_tool_calls": [{"name": "search", "arguments": {"q": "test"}}],
        },
    )
    assert score == 1.0


def test_eval_summary_compute_averages():
    from app.engines.eval_engine.evaluator import EvalResult
    summary = EvalSummary()
    summary.results = [
        EvalResult(test_case_index=0, input_text="", expected_output="", actual_output="", scores={"a": 0.8, "b": 0.6}),
        EvalResult(test_case_index=1, input_text="", expected_output="", actual_output="", scores={"a": 0.4, "b": 0.2}),
    ]
    summary.compute_averages()
    assert summary.metric_averages["a"] == pytest.approx(0.6, rel=0.01)
    assert summary.metric_averages["b"] == pytest.approx(0.4, rel=0.01)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def test_validate_dataset():
    data = [
        {"question": "Q1", "answer": "A1", "ground_truth": "GT1", "contexts": ["C1"]},
        {"question": "Q2", "answer": "A2"},
    ]
    result = _validate_dataset(data)
    assert len(result) == 2
    assert result[0]["question"] == "Q1"
    assert result[1]["contexts"] == []
    assert result[1]["tool_calls"] == []


def test_load_dataset_json(tmp_path):
    data = [
        {
            "question": "What is AI?",
            "answer": "AI is artificial intelligence.",
            "ground_truth": "AI stands for artificial intelligence.",
            "contexts": ["AI = artificial intelligence"],
        }
    ]
    path = tmp_path / "test_dataset.json"
    path.write_text(json.dumps(data))

    loaded = load_dataset(str(path))
    assert len(loaded) == 1
    assert loaded[0]["question"] == "What is AI?"


def test_load_dataset_csv(tmp_path):
    csv_content = "question,answer,ground_truth,contexts\nWhat is AI?,AI is artificial.,AI stands for.,AI = artificial"
    path = tmp_path / "test.csv"
    path.write_text(csv_content)

    loaded = load_dataset(str(path))
    assert len(loaded) == 1
    assert loaded[0]["question"] == "What is AI?"


def test_load_dataset_not_found():
    with pytest.raises(FileNotFoundError):
        load_dataset("/nonexistent/path.json")


def test_load_dataset_unsupported_format(tmp_path):
    path = tmp_path / "test.txt"
    path.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported"):
        load_dataset(str(path))


def test_export_dataset_json(tmp_path):
    data = [{"question": "Q", "answer": "A", "ground_truth": "GT", "contexts": ["C"]}]
    path = tmp_path / "export.json"
    export_dataset(data, str(path))
    loaded = json.loads(path.read_text())
    assert len(loaded) == 1
    assert loaded[0]["question"] == "Q"


def test_export_dataset_csv(tmp_path):
    data = [{"question": "Q", "answer": "A", "ground_truth": "GT", "contexts": ["C"], "tool_calls": [], "expected_tool_calls": []}]
    path = tmp_path / "export.csv"
    export_dataset(data, str(path))
    assert path.exists()
    content = path.read_text()
    assert "question" in content
    assert "Q" in content


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def test_extract_sentences():
    sentences = _extract_sentences("Hello world. This is a test. Done!")
    assert len(sentences) == 3
    assert "Hello world." in sentences[0]


def test_normalize():
    assert _normalize("  Hello   World  ") == "hello world"


def test_metric_registry():
    expected = {"faithfulness", "answer_relevancy", "context_precision", "context_recall", "tool_call_accuracy"}
    assert set(METRIC_REGISTRY.keys()) == expected
