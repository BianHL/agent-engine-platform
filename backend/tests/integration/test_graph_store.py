"""Integration tests for Neo4j Graph Store operations (K-005, K-006, K-007, K-008).
Verifies code logic by mocking the Neo4j driver at the connection level."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.engines.knowledge_engine.storage.graph.neo4j_store import (
    Neo4jGraphStore,
    ALLOWED_LABELS,
    ALLOWED_RELATIONS,
    _validate_label,
    _validate_relation_type,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _async_context_manager(mock_obj):
    """Wrap *mock_obj* so it works with ``async with``."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_obj)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _make_store_with_mock_driver():
    """Return a ``Neo4jGraphStore`` whose ``_driver`` is a fully-mocked async driver."""
    store = Neo4jGraphStore(uri="bolt://fake:7687", user="neo4j", password="test")
    mock_session = AsyncMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value = _async_context_manager(mock_session)
    store._driver = mock_driver
    return store, mock_session


# ---------------------------------------------------------------------------
# K-005 -- create_node
# ---------------------------------------------------------------------------

class TestCreateNode:
    """K-005: Neo4jGraphStore.create_node() with mocked driver."""

    @pytest.mark.asyncio
    async def test_create_node_returns_element_id(self):
        store, mock_session = _make_store_with_mock_driver()

        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"id": "4:abc:1"})
        mock_session.run = AsyncMock(return_value=mock_result)

        node_id = await store.create_node("Person", {"name": "Alice", "age": 30})

        assert node_id == "4:abc:1"
        mock_session.run.assert_awaited_once()
        call_args = mock_session.run.call_args
        # Cypher should contain the validated label
        assert "Person" in call_args[0][0]
        # Properties should be passed as the ``props`` parameter
        assert call_args[1]["props"] == {"name": "Alice", "age": 30}

    @pytest.mark.asyncio
    async def test_create_node_rejects_unknown_label(self):
        store, _ = _make_store_with_mock_driver()

        with pytest.raises(ValueError, match="not allowed"):
            await store.create_node("HackerNode", {"evil": True})

    @pytest.mark.asyncio
    async def test_create_node_all_allowed_labels(self):
        """Every label in the whitelist should be accepted."""
        store, mock_session = _make_store_with_mock_driver()

        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"id": "0"})
        mock_session.run = AsyncMock(return_value=mock_result)

        for label in ALLOWED_LABELS:
            node_id = await store.create_node(label, {"test": True})
            assert node_id == "0"


# ---------------------------------------------------------------------------
# K-006 -- Cypher injection prevention
# ---------------------------------------------------------------------------

class TestCypherInjectionPrevention:
    """K-006: _validate_label() and _validate_relation_type() reject malicious input."""

    # -- _validate_label ----------------------------------------------------

    @pytest.mark.parametrize("bad_label", [
        "Person) DETACH DELETE n//",
        "Person; MATCH (n) DETACH DELETE n",
        "Person` OR 1=1",
        "Person\nDETACH DELETE",
        "",
        "123Start",
        "Has Space",
        "Has-Dash",
    ])
    def test_validate_label_rejects_injection(self, bad_label):
        with pytest.raises(ValueError):
            _validate_label(bad_label)

    def test_validate_label_accepts_valid(self):
        assert _validate_label("Person") == "Person"
        assert _validate_label("Entity") == "Entity"
        assert _validate_label("Organization") == "Organization"

    # -- _validate_relation_type --------------------------------------------

    @pytest.mark.parametrize("bad_rel", [
        "RELATED_TO) DETACH DELETE n//",
        "RELATED_TO; DROP DATABASE",
        "NOT_IN_WHITELIST",
        "",
        "contains",  # wrong case
    ])
    def test_validate_relation_type_rejects_injection(self, bad_rel):
        with pytest.raises(ValueError):
            _validate_relation_type(bad_rel)

    def test_validate_relation_type_accepts_valid(self):
        assert _validate_relation_type("RELATED_TO") == "RELATED_TO"
        assert _validate_relation_type("CONTAINS") == "CONTAINS"

    # -- create_node should not reach driver on bad label -------------------

    @pytest.mark.asyncio
    async def test_create_node_blocks_injection_before_driver(self):
        store, mock_session = _make_store_with_mock_driver()

        with pytest.raises(ValueError):
            await store.create_node("Person) DETACH DELETE n//", {"x": 1})

        # The driver should never have been called
        mock_session.run.assert_not_awaited()

    # -- create_relation should not reach driver on bad relation type -------

    @pytest.mark.asyncio
    async def test_create_relation_blocks_injection_before_driver(self):
        store, mock_session = _make_store_with_mock_driver()

        with pytest.raises(ValueError):
            await store.create_relation("a", "b", "RELATED_TO) DETACH DELETE n//")

        mock_session.run.assert_not_awaited()


# ---------------------------------------------------------------------------
# K-007 -- create_relation
# ---------------------------------------------------------------------------

class TestCreateRelation:
    """K-007: Neo4jGraphStore.create_relation() with mocked driver."""

    @pytest.mark.asyncio
    async def test_create_relation_calls_driver(self):
        store, mock_session = _make_store_with_mock_driver()
        mock_session.run = AsyncMock()

        await store.create_relation("4:abc:1", "4:abc:2", "RELATED_TO", {"weight": 0.9})

        mock_session.run.assert_awaited_once()
        call_args = mock_session.run.call_args
        cypher = call_args[0][0]
        assert "RELATED_TO" in cypher
        assert call_args[1]["from_id"] == "4:abc:1"
        assert call_args[1]["to_id"] == "4:abc:2"
        assert call_args[1]["props"] == {"weight": 0.9}

    @pytest.mark.asyncio
    async def test_create_relation_default_empty_props(self):
        store, mock_session = _make_store_with_mock_driver()
        mock_session.run = AsyncMock()

        await store.create_relation("a", "b", "CONTAINS")

        call_args = mock_session.run.call_args
        assert call_args[1]["props"] == {}

    @pytest.mark.asyncio
    async def test_create_relation_all_allowed_types(self):
        """Every relation type in the whitelist should be accepted."""
        store, mock_session = _make_store_with_mock_driver()
        mock_session.run = AsyncMock()

        for rel_type in ALLOWED_RELATIONS:
            await store.create_relation("a", "b", rel_type)

        assert mock_session.run.await_count == len(ALLOWED_RELATIONS)

    @pytest.mark.asyncio
    async def test_create_relation_rejects_unknown_type(self):
        store, _ = _make_store_with_mock_driver()

        with pytest.raises(ValueError, match="not allowed"):
            await store.create_relation("a", "b", "MALICIOUS_REL")


# ---------------------------------------------------------------------------
# K-008 -- get_neighbors with depth parameter
# ---------------------------------------------------------------------------

class TestGetNeighbors:
    """K-008: Neo4jGraphStore.get_neighbors() with depth parameter."""

    @staticmethod
    def _make_record(node_id, labels, props, depth):
        """Build a mock record that mimics the Neo4j driver's record shape."""
        node = MagicMock()
        node.element_id = node_id
        node.__iter__ = MagicMock(return_value=iter(props.items()))
        # dict(node) should return props
        node.keys.return_value = list(props.keys())
        node.__getitem__ = lambda self, key: props[key]

        record = MagicMock()
        record.__getitem__ = lambda self, key: {
            "neighbor": node,
            "labels": labels,
            "depth": depth,
        }[key]
        return record

    @pytest.mark.asyncio
    async def test_get_neighbors_returns_parsed_nodes(self):
        store, mock_session = _make_store_with_mock_driver()

        records = [
            self._make_record("4:abc:2", ["Person"], {"name": "Bob"}, 1),
            self._make_record("4:abc:3", ["Document"], {"title": "Doc1"}, 2),
        ]

        mock_result = MagicMock()

        async def _aiter(self_result):
            for r in records:
                yield r

        mock_result.__aiter__ = _aiter
        mock_session.run = AsyncMock(return_value=mock_result)

        neighbors = await store.get_neighbors("4:abc:1", depth=2)

        assert len(neighbors) == 2
        assert neighbors[0]["id"] == "4:abc:2"
        assert neighbors[0]["labels"] == ["Person"]
        assert neighbors[0]["properties"]["name"] == "Bob"
        assert neighbors[0]["depth"] == 1
        assert neighbors[1]["id"] == "4:abc:3"
        assert neighbors[1]["depth"] == 2

    @pytest.mark.asyncio
    async def test_get_neighbors_depth_clamped_to_min(self):
        """Depth < 1 should be clamped to 1."""
        store, mock_session = _make_store_with_mock_driver()

        mock_result = MagicMock()
        mock_result.__aiter__ = lambda self: self._aiter_impl()

        async def _empty_aiter():
            return
            yield  # make it an async generator

        mock_result.__aiter__ = lambda self: _empty_aiter()
        mock_session.run = AsyncMock(return_value=mock_result)

        await store.get_neighbors("4:abc:1", depth=0)

        cypher = mock_session.run.call_args[0][0]
        assert "*1..1" in cypher

    @pytest.mark.asyncio
    async def test_get_neighbors_depth_clamped_to_max(self):
        """Depth > 5 should be clamped to 5."""
        store, mock_session = _make_store_with_mock_driver()

        async def _empty_aiter():
            return
            yield

        mock_result = MagicMock()
        mock_result.__aiter__ = lambda self: _empty_aiter()
        mock_session.run = AsyncMock(return_value=mock_result)

        await store.get_neighbors("4:abc:1", depth=99)

        cypher = mock_session.run.call_args[0][0]
        assert "*1..5" in cypher

    @pytest.mark.asyncio
    async def test_get_neighbors_default_depth(self):
        """Default depth should be 1."""
        store, mock_session = _make_store_with_mock_driver()

        async def _empty_aiter():
            return
            yield

        mock_result = MagicMock()
        mock_result.__aiter__ = lambda self: _empty_aiter()
        mock_session.run = AsyncMock(return_value=mock_result)

        await store.get_neighbors("4:abc:1")

        cypher = mock_session.run.call_args[0][0]
        assert "*1..1" in cypher

    @pytest.mark.asyncio
    async def test_get_neighbors_empty_result(self):
        store, mock_session = _make_store_with_mock_driver()

        async def _empty_aiter():
            return
            yield

        mock_result = MagicMock()
        mock_result.__aiter__ = lambda self: _empty_aiter()
        mock_session.run = AsyncMock(return_value=mock_result)

        neighbors = await store.get_neighbors("4:abc:1", depth=1)
        assert neighbors == []


# ---------------------------------------------------------------------------
# ALLOWED_LABELS / ALLOWED_RELATIONS whitelist sanity
# ---------------------------------------------------------------------------

class TestWhitelists:
    """Verify the ALLOWED_LABELS and ALLOWED_RELATIONS whitelists are well-formed."""

    def test_allowed_labels_non_empty(self):
        assert len(ALLOWED_LABELS) > 0

    def test_allowed_labels_are_strings(self):
        for label in ALLOWED_LABELS:
            assert isinstance(label, str)
            assert len(label) > 0

    def test_allowed_labels_match_identifier_format(self):
        import re
        for label in ALLOWED_LABELS:
            assert re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", label), f"Label '{label}' is not a valid identifier"

    def test_allowed_relations_non_empty(self):
        assert len(ALLOWED_RELATIONS) > 0

    def test_allowed_relations_are_uppercase(self):
        for rel in ALLOWED_RELATIONS:
            assert rel == rel.upper(), f"Relation '{rel}' should be uppercase"

    def test_allowed_relations_no_whitespace(self):
        for rel in ALLOWED_RELATIONS:
            assert " " not in rel, f"Relation '{rel}' contains whitespace"
