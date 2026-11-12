from pathlib import Path
from typing import Optional, Union

import httpx

from .gqlauth import GraphqlAuth, AuthenticationType
from .gqlclient import Client
from .base_operation import GraphQLField
from .auth.device_authorization_flow import DevicePromptHandler


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
        device_prompt: Optional[DevicePromptHandler] = None,
    ):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_file=token_file,
            port=port,
            type=authentication_type,
            base_url=base_url,
            device_prompt=device_prompt,
        )
        self.client = Client(
            url=self.graphql_url,
            http_client=httpx.AsyncClient(auth=self.httpx_auth),
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
