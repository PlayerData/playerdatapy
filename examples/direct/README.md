# Direct GraphQL Examples

This folder contains examples demonstrating how to use PlayerDataPy by directly interacting with the `GraphqlClient` class. This approach gives you full control over GraphQL query strings and is useful when you need fine-grained control or want to use queries from external sources.

## Overview

The direct approach uses the `GraphqlClient` class to execute raw GraphQL query strings. This method is more flexible but requires you to manually construct GraphQL queries and handle the response structure.

## Quick Start

The simplest way to get started is with the `quick_start.py` example:

```bash
python examples/direct/quick_start.py
```

Before running, set the following environment variables:

```bash
export CLIENT_ID=your_client_id
export CLIENT_SECRET=your_client_secret
export CLUB_ID=your_club_id
```

## Basic Usage Pattern

```python
from playerdatapy.gqlauth import GraphqlAuth, AuthenticationType
from playerdatapy.gqlclient import Client
from playerdatapy.constants import API_BASE_URL
import asyncio

# Authenticate
auth = GraphqlAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    type=AuthenticationType.CLIENT_CREDENTIALS_FLOW,
)

# Create a Client instance
client = Client(
    url=f"{API_BASE_URL}/api/graphql",
    headers={"Authorization": f"Bearer {auth._get_authentication_token()}"},
)

# Build your GraphQL query string
query = """
query($clubIdEq:ID!,$startTimeGteq:ISO8601DateTime,$endTimeLteq:ISO8601DateTime){
  sessions(filter: {clubIdEq:$clubIdEq, startTimeGteq:$startTimeGteq, endTimeLteq:$endTimeLteq}){
    id
    startTime
    endTime
  }
}
"""

# Define variables
variables = {
    "clubIdEq": CLUB_ID,
    "startTimeGteq": start_time,
    "endTimeLteq": end_time,
}

# Execute the query
async def main():
    response = client.execute(query=query, variables=variables)
    result = await client.get_data(response)
    print(result["sessions"])

asyncio.run(main())
```

## Building Queries

When building GraphQL queries, you can use the GraphiQL Playground at https://app.playerdata.co.uk/api/graphiql/ to:
- Test queries interactively
- Explore the schema
- Validate query syntax
- See example queries

The playground provides autocomplete and schema documentation to help you build queries efficiently.

## Example Query

The `quick_start.py` example demonstrates querying sessions filtered by time range:

```graphql
query($clubIdEq:ID!,$startTimeGteq:ISO8601DateTime,$endTimeLteq:ISO8601DateTime){
  sessions(filter: {clubIdEq:$clubIdEq, startTimeGteq:$startTimeGteq, endTimeLteq:$endTimeLteq}){
    id
    startTime
    endTime
  }
}
```

This query:
- Takes a club ID and time range as variables
- Filters sessions by club ID and time range
- Returns session ID, start time, and end time

## Authentication Types

The examples use `AuthenticationType.CLIENT_CREDENTIALS_FLOW` by default, which is suitable for backend-to-backend communication. You can also use:

- `AuthenticationType.AUTHORISATION_CODE_FLOW`: For confidential client credentials
- `AuthenticationType.AUTHORISATION_CODE_FLOW_PKCE`: For non-confidential client credentials

## When to Use Direct GraphQL

Use the direct GraphQL approach when:
- You need full control over query strings
- You're migrating existing GraphQL queries
- You want to use queries from external tools or documentation
- You prefer working with raw GraphQL syntax

For type-safe queries with autocomplete support, consider using the [Pydantic examples](../pydantic/) instead.
