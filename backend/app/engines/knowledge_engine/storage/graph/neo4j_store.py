from neo4j import AsyncGraphDatabase
from typing import Optional
import re

ALLOWED_LABELS = {
    "Person", "Organization", "Concept", "Event", "Document",
    "Entity", "Topic", "Skill", "Location", "Product",
}
ALLOWED_RELATIONS = {
    "RELATED_TO", "CONTAINS", "MENTIONS", "DEPENDS_ON", "CREATED_BY",
    "BELONGS_TO", "KNOWS", "TEACHES", "USES", "PART_OF",
}


def _validate_label(label: str) -> str:
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Label '{label}' not allowed. Allowed: {ALLOWED_LABELS}")
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", label):
        raise ValueError(f"Invalid label format: {label}")
    return label


def _validate_relation_type(rel: str) -> str:
    if rel not in ALLOWED_RELATIONS:
        raise ValueError(f"Relation type '{rel}' not allowed. Allowed: {ALLOWED_RELATIONS}")
    return rel


class Neo4jGraphStore:
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self._driver = None

    async def connect(self):
        self._driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))

    async def close(self):
        if self._driver:
            await self._driver.close()

    async def create_node(self, label: str, properties: dict) -> str:
        label = _validate_label(label)
        async with self._driver.session() as session:
            result = await session.run(
                f"CREATE (n:{label} $props) RETURN elementId(n) AS id",
                props=properties,
            )
            record = await result.single()
            return record["id"]

    async def merge_node(self, label: str, key: str, properties: dict) -> str:
        """MERGE a node by label + key property. Creates if not exists, updates if exists."""
        label = _validate_label(label)
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            raise ValueError(f"Invalid merge key: {key}")
        async with self._driver.session() as session:
            result = await session.run(
                f"MERGE (n:{label} {{{key}: $value}}) "
                f"SET n += $props "
                f"RETURN elementId(n) AS id",
                value=properties.get(key, ""),
                props=properties,
            )
            record = await result.single()
            return record["id"]

    async def create_relation(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        properties: dict = None,
    ):
        relation_type = _validate_relation_type(relation_type)
        async with self._driver.session() as session:
            await session.run(
                f"MATCH (a), (b) WHERE elementId(a) = $from_id AND elementId(b) = $to_id "
                f"CREATE (a)-[r:{relation_type} $props]->(b)",
                from_id=from_id,
                to_id=to_id,
                props=properties or {},
            )

    async def get_neighbors(self, node_id: str, depth: int = 1) -> list[dict]:
        depth = max(1, min(5, depth))
        async with self._driver.session() as session:
            result = await session.run(
                f"MATCH path = (start)-[*1..{depth}]-(neighbor) "
                f"WHERE elementId(start) = $node_id "
                f"RETURN DISTINCT neighbor, labels(neighbor) AS labels, length(path) AS depth",
                node_id=node_id,
            )
            nodes = []
            async for record in result:
                node = record["neighbor"]
                nodes.append(
                    {
                        "id": node.element_id,
                        "labels": record["labels"],
                        "properties": dict(node),
                        "depth": record["depth"],
                    }
                )
            return nodes

    async def search_nodes(self, query: str, limit: int = 10) -> list[dict]:
        async with self._driver.session() as session:
            result = await session.run(
                "MATCH (n) WHERE any(prop IN keys(n) WHERE toString(n[prop]) CONTAINS $query) "
                "RETURN n, labels(n) AS labels LIMIT $limit",
                query=query,
                limit=limit,
            )
            nodes = []
            async for record in result:
                node = record["n"]
                nodes.append(
                    {
                        "id": node.element_id,
                        "labels": record["labels"],
                        "properties": dict(node),
                    }
                )
            return nodes

    async def delete_node(self, node_id: str):
        async with self._driver.session() as session:
            await session.run(
                "MATCH (n) WHERE elementId(n) = $node_id DETACH DELETE n",
                node_id=node_id,
            )

    async def build_graph_from_entities(self, entities: list, relations: list) -> dict:
        node_ids = {}
        async with self._driver.session() as session:
            for entity in entities:
                label = _validate_label(entity.get("type", "Entity"))
                result = await session.run(
                    f"MERGE (n:{label} {{name: $name}}) "
                    f"SET n.description = $description "
                    f"RETURN elementId(n) AS id",
                    name=entity["name"],
                    description=entity.get("description", ""),
                )
                record = await result.single()
                node_ids[entity["name"]] = record["id"]

            for rel in relations:
                from_name = rel.get("from_entity", rel.get("from"))
                to_name = rel.get("to_entity", rel.get("to"))
                rel_type = _validate_relation_type(
                    rel.get("relation_type", rel.get("type", "RELATED_TO"))
                )
                from_id = node_ids.get(from_name)
                to_id = node_ids.get(to_name)
                if from_id and to_id:
                    await session.run(
                        f"MATCH (a), (b) WHERE elementId(a) = $from_id AND elementId(b) = $to_id "
                        f"MERGE (a)-[r:{rel_type}]->(b)",
                        from_id=from_id,
                        to_id=to_id,
                    )
        return node_ids
