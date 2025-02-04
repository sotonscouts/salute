from strawberry_django.test.client import Response, TestClient

from salute.api.schema import schema


class TestSchema:
    PING_QUERY = """
    query {
        ping
    }
    """

    def test_ping_query(self) -> None:
        result = schema.execute_sync(self.PING_QUERY)
        assert result.errors is None
        assert result.data == {"ping": "pong"}

    def test_ping_query_http(self) -> None:
        client = TestClient("/graphql/")
        result = client.query(self.PING_QUERY)
        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {"ping": "pong"}
