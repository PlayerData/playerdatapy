from pathlib import Path
from typing import Optional, Union

from .gqlauth import GraphqlAuth, AuthenticationType
from .gqlclient import Client
from .base_operation import GraphQLField
from playerdatapy.constants import GRAPHQL_URL, graphql_url_for


class PlayerDataAPI(GraphqlAuth):
    def __init__(
        self,
        client_id: str,
        client_secret: str = "",
        redirect_uri: str = "http://localhost:8888",
        token_file: Optional[Union[str, Path]] = None,
        port: int = 8888,
        authentication_type: AuthenticationType = AuthenticationType.AUTHORISATION_CODE_FLOW,
        base_url: Optional[str] = None,
    ):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_file=token_file,
            port=port,
            type=authentication_type,
            base_url=base_url,
        )
        graphql_url = graphql_url_for(base_url) if base_url else GRAPHQL_URL
        self.client = Client(
            url=graphql_url,
            headers={"Authorization": f"Bearer {self._get_authentication_token()}"},
        )

    async def run_queries(self, operation_name: str, *query_objects: GraphQLField):
        response = await self.client.query(
            *query_objects,
            operation_name=operation_name,
        )
        return response

    async def run_mutations(self, operation_name: str, *mutation_objects: GraphQLField):
        response = await self.client.mutation(
            *mutation_objects,
            operation_name=operation_name,
        )
        return response
