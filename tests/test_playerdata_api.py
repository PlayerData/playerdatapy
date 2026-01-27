from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from playerdatapy.playerdata_api import PlayerDataAPI
from playerdatapy.gqlauth import AuthenticationType
from playerdatapy.base_operation import GraphQLField


class TestPlayerdataAPI:
    """Tests for PlayerDataAPI class."""

    @patch("playerdatapy.playerdata_api.Client")
    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.ClientCredentialsFlow")
    def test_init(self, mock_flow_class, mock_session_class, mock_client_class):
        """Test PlayerDataAPI initialization."""
        # Setup mocks for GraphqlAuth initialization
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        interface = PlayerDataAPI(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:9999",
            token_file=".test_token",
            port=9999,
            authentication_type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
        )

        # Verify Client was initialized with correct URL and headers
        mock_client_class.assert_called_once_with(
            url="https://app.playerdata.co.uk/api/graphql",
            headers={"Authorization": "Bearer test_token"},
        )

        assert interface.client == mock_client_instance

    @patch("playerdatapy.playerdata_api.Client")
    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.AuthorisationCodeFlow")
    def test_init_defaults(
        self, mock_flow_class, mock_session_class, mock_client_class
    ):
        """Test PlayerDataAPI initialization with default values."""
        # Setup mocks for GraphqlAuth initialization
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "default_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "default_token"}
        mock_session_class.return_value = mock_session

        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        interface = PlayerDataAPI(client_id="test_client")

        assert interface.client_id == "test_client"
        assert interface.client_secret == ""
        assert interface.redirect_uri == "http://localhost:8888"
        assert interface.token_file == ".token"
        assert interface.port == 8888
        assert (
            interface.authentication_type == AuthenticationType.AUTHORISATION_CODE_FLOW
        )
        assert interface.client == mock_client_instance

    @pytest.mark.asyncio
    @patch("playerdatapy.playerdata_api.Client")
    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.ClientCredentialsFlow")
    async def test_run_queries(
        self, mock_flow_class, mock_session_class, mock_client_class
    ):
        """Test run_queries method calls client.query with correct parameters."""
        # Setup mocks for GraphqlAuth initialization
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        mock_client_instance = MagicMock()
        mock_client_instance.query = AsyncMock(
            return_value={"data": {"test": "result"}}
        )
        mock_client_class.return_value = mock_client_instance

        interface = PlayerDataAPI(
            client_id="test_client",
            client_secret="test_secret",
            authentication_type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
        )

        query1 = MagicMock(spec=GraphQLField)
        query2 = MagicMock(spec=GraphQLField)

        result = await interface.run_queries("TestQuery", query1, query2)

        mock_client_instance.query.assert_called_once_with(
            query1, query2, operation_name="TestQuery"
        )
        assert result == {"data": {"test": "result"}}

    @pytest.mark.asyncio
    @patch("playerdatapy.playerdata_api.Client")
    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.AuthorisationCodeFlow")
    async def test_run_queries_single_query(
        self, mock_flow_class, mock_session_class, mock_client_class
    ):
        """Test run_queries with a single query object."""
        # Setup mocks for GraphqlAuth initialization
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        mock_client_instance = MagicMock()
        mock_client_instance.query = AsyncMock(
            return_value={"data": {"athlete": {"id": "123"}}}
        )
        mock_client_class.return_value = mock_client_instance

        interface = PlayerDataAPI(client_id="test_client")

        query = MagicMock(spec=GraphQLField)
        result = await interface.run_queries("GetAthlete", query)

        mock_client_instance.query.assert_called_once_with(
            query, operation_name="GetAthlete"
        )
        assert result == {"data": {"athlete": {"id": "123"}}}

    @pytest.mark.asyncio
    @patch("playerdatapy.playerdata_api.Client")
    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.AuthorisationCodeFlow")
    async def test_run_queries_empty(
        self, mock_flow_class, mock_session_class, mock_client_class
    ):
        """Test run_queries with no queries."""
        # Setup mocks for GraphqlAuth initialization
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        mock_client_instance = MagicMock()
        mock_client_instance.query = AsyncMock(
            return_value={"data": {"result": "success"}}
        )
        mock_client_class.return_value = mock_client_instance

        interface = PlayerDataAPI(client_id="test_client")

        result = await interface.run_queries("EmptyQuery")

        mock_client_instance.query.assert_called_once_with(operation_name="EmptyQuery")
        assert result == {"data": {"result": "success"}}

    @pytest.mark.asyncio
    @patch("playerdatapy.playerdata_api.Client")
    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.ClientCredentialsFlow")
    async def test_run_mutations(
        self, mock_flow_class, mock_session_class, mock_client_class
    ):
        """Test run_mutations method calls client.mutation with correct parameters."""
        # Setup mocks for GraphqlAuth initialization
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        mock_client_instance = MagicMock()
        mock_client_instance.mutation = AsyncMock(
            return_value={"data": {"createAthlete": {"id": "123"}}}
        )
        mock_client_class.return_value = mock_client_instance

        interface = PlayerDataAPI(
            client_id="test_client",
            client_secret="test_secret",
            authentication_type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
        )

        # Create mock mutation objects
        mutation1 = MagicMock(spec=GraphQLField)
        mutation2 = MagicMock(spec=GraphQLField)

        result = await interface.run_mutations("CreateAthlete", mutation1, mutation2)

        mock_client_instance.mutation.assert_called_once_with(
            mutation1, mutation2, operation_name="CreateAthlete"
        )
        assert result == {"data": {"createAthlete": {"id": "123"}}}

    @pytest.mark.asyncio
    @patch("playerdatapy.playerdata_api.Client")
    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.AuthorisationCodeFlow")
    async def test_run_mutations_single_mutation(
        self, mock_flow_class, mock_session_class, mock_client_class
    ):
        """Test run_mutations with a single mutation object."""
        # Setup mocks for GraphqlAuth initialization
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        mock_client_instance = MagicMock()
        mock_client_instance.mutation = AsyncMock(
            return_value={"data": {"updateAthlete": {"success": True}}}
        )
        mock_client_class.return_value = mock_client_instance

        interface = PlayerDataAPI(client_id="test_client")

        mutation = MagicMock(spec=GraphQLField)
        result = await interface.run_mutations("UpdateAthlete", mutation)

        mock_client_instance.mutation.assert_called_once_with(
            mutation, operation_name="UpdateAthlete"
        )
        assert result == {"data": {"updateAthlete": {"success": True}}}

    @pytest.mark.asyncio
    @patch("playerdatapy.playerdata_api.Client")
    @patch("playerdatapy.gqlauth.OAuth2Session")
    @patch("playerdatapy.gqlauth.AuthorisationCodeFlow")
    async def test_run_mutations_empty(
        self, mock_flow_class, mock_session_class, mock_client_class
    ):
        """Test run_mutations with no mutations."""
        # Setup mocks for GraphqlAuth initialization
        mock_authenticator = MagicMock()
        mock_authenticator.get_token.return_value = {"access_token": "test_token"}
        mock_flow_class.return_value = mock_authenticator

        mock_session = MagicMock()
        mock_session.token = {"access_token": "test_token"}
        mock_session_class.return_value = mock_session

        mock_client_instance = MagicMock()
        mock_client_instance.mutation = AsyncMock(
            return_value={"data": {"result": "success"}}
        )
        mock_client_class.return_value = mock_client_instance

        interface = PlayerDataAPI(client_id="test_client")

        result = await interface.run_mutations("EmptyMutation")

        mock_client_instance.mutation.assert_called_once_with(
            operation_name="EmptyMutation"
        )
        assert result == {"data": {"result": "success"}}
