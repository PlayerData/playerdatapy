from unittest.mock import AsyncMock

import pytest
from graphql import Node

from playerdatapy.custom_fields import TrainingSessionFields
from playerdatapy.custom_queries import Query
from playerdatapy.gqlclient import Client


def _client() -> Client:
    client = Client(url="https://example.test/api/graphql")
    client.execute = AsyncMock()
    client.get_data = lambda response: response
    return client


def _session_query():
    return Query.session(id="session-id").on(
        "TrainingSession", TrainingSessionFields.id
    )


def _lists_in(node: Node, path: str = "document") -> list[str]:
    found = []
    for key in node.keys:
        value = getattr(node, key)
        where = f"{path}.{key}"
        if isinstance(value, list):
            found.append(where)
        if isinstance(value, Node):
            found += _lists_in(value, where)
        if isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                found += _lists_in(child, f"{where}[{index}]")
    return found


class TestQueryDocuments:
    """The documents the client builds, as graphql-core 3.3 needs them: 3.3
    only prints a document whose node collections are tuples."""

    def test_document_collections_are_tuples(self):
        client = _client()
        fields = (_session_query(),)
        variables = client._combine_variables(fields)

        document = client._build_operation_ast(
            tuple(client._build_selection_set(fields)),
            operation_type="query",
            operation_name="Session",
            variable_definitions=client._build_variable_definitions(variables["types"]),
        )

        assert _lists_in(document) == []

    @pytest.mark.asyncio
    async def test_query_sends_the_printed_document(self):
        client = _client()

        await client.query(_session_query(), operation_name="Session")

        (query,) = client.execute.await_args.args
        assert " ".join(query.split()) == (
            "query Session($id_0: ID!) { session(id: $id_0) "
            "{ ... on TrainingSession { id } } }"
        )
