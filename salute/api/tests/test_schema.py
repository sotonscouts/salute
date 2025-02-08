from http import HTTPStatus

from django.test import Client as DjangoTestClient
from django.test import override_settings
from django.urls import reverse
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User


class TestSchema:
    PING_QUERY = """
    query {
        ping
    }
    """

    def test_ping__not_authenticated(self) -> None:
        client = TestClient("/graphql/")
        results = client.query(self.PING_QUERY, assert_no_errors=False)

        assert isinstance(results, Response)

        assert results.errors == [
            {"message": "User is not authenticated.", "locations": [{"line": 3, "column": 9}], "path": ["ping"]}
        ]
        assert results.data is None

    def test_ping__authenticated(self, admin_user: User) -> None:
        client = TestClient("/graphql/")
        with client.login(admin_user):
            result = client.query(self.PING_QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {"ping": "pong"}


class TestGraphiQLDisabledWhenAnonymous:
    url = reverse("graphql")

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=False)
    def test_graphiql_disabled(self, client: DjangoTestClient) -> None:
        resp = client.get(self.url, headers={"Accept": "text/html"})

        assert resp.status_code == HTTPStatus.NOT_FOUND
        assert b"Not Found" in resp.content

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=False)
    def test_graphiql_disabled__authenticated(self, client: DjangoTestClient, admin_user: User) -> None:
        client.force_login(admin_user)
        resp = client.get(self.url, headers={"Accept": "text/html"})

        assert resp.status_code == HTTPStatus.OK
        assert b"GraphiQL" in resp.content

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=True)
    def test_graphiql_enabled(self, client: DjangoTestClient) -> None:
        resp = client.get(self.url, headers={"Accept": "text/html"})

        assert resp.status_code == HTTPStatus.OK
        assert b"GraphiQL" in resp.content

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=True)
    def test_graphiql_enabled__authenticated(self, client: DjangoTestClient, admin_user: User) -> None:
        client.force_login(admin_user)
        resp = client.get(self.url, headers={"Accept": "text/html"})

        assert resp.status_code == HTTPStatus.OK
        assert b"GraphiQL" in resp.content

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=True)
    def test_get__not_authenticated(
        self,
        client: DjangoTestClient,
    ) -> None:
        resp = client.get(self.url)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=True)
    def test_get__authenticated(self, client: DjangoTestClient, admin_user: User) -> None:
        client.force_login(admin_user)
        resp = client.get(self.url)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=False)
    def test_get__disabled__not_authenticated(
        self,
        client: DjangoTestClient,
    ) -> None:
        resp = client.get(self.url)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=False)
    def test_get__disabled__authenticated(self, client: DjangoTestClient, admin_user: User) -> None:
        client.force_login(admin_user)
        resp = client.get(self.url)

        assert resp.status_code == HTTPStatus.BAD_REQUEST


class TestNoIntrospection:
    INTROSPECTION_QUERY = """
    query {
        __schema {
            types {
                name
            }
        }
    }
    """

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=True)
    def test_introspection__enabled__not_authenticated(self) -> None:
        client = TestClient("/graphql/")
        result = client.query(self.INTROSPECTION_QUERY, assert_no_errors=False)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data is not None
        assert "__schema" in result.data

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=False)
    def test_introspection__not_authenticated(self) -> None:
        client = TestClient("/graphql/")
        results = client.query(self.INTROSPECTION_QUERY, assert_no_errors=False)

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "GraphQL introspection has been disabled, but the requested query contained the field '__schema'.",  # noqa: E501
                "locations": [{"line": 3, "column": 9}],
            },
            {
                "message": "GraphQL introspection has been disabled, but the requested query contained the field 'types'.",  # noqa: E501
                "locations": [{"line": 4, "column": 13}],
            },
        ]
        assert results.data is None

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=True)
    def test_introspection__enabled__authenticated(self, admin_user: User) -> None:
        client = TestClient("/graphql/")
        with client.login(admin_user):
            result = client.query(self.INTROSPECTION_QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data is not None
        assert "__schema" in result.data

    @override_settings(ALLOW_UNAUTHENTICATED_GRAPHIQL=False)
    def test_introspection__authenticated(self, admin_user: User) -> None:
        client = TestClient("/graphql/")
        with client.login(admin_user):
            result = client.query(self.INTROSPECTION_QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data is not None
        assert "__schema" in result.data
