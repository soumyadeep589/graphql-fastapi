from collections import defaultdict
from time import time
from fastapi import FastAPI, Request
from ariadne import (
    QueryType,
    gql,
    make_executable_schema,
    format_error as default_format_error,
)
from ariadne.asgi import GraphQL
from requests.exceptions import RequestException
from slowapi.errors import RateLimitExceeded
import requests


# Define GraphQL schema in SDL (Schema Definition Language)
type_defs = gql(
    """
    type Query {
        users: [User!]!
    }

    type User {
        id: ID!
        name: String!
        email: String!
        address: Address!
    }
    
    type Address {
        street: String!
        city: String!
        zipcode: String!
    }
"""
)


class RateLimitExceededException(Exception):
    pass


class InMemoryRateLimiter:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.requests = defaultdict(list)

    def is_rate_limited(self, client_id: str) -> bool:
        current_time = time()
        # Remove outdated requests
        self.requests[client_id] = [
            timestamp
            for timestamp in self.requests[client_id]
            if current_time - timestamp < self.window
        ]

        if len(self.requests[client_id]) >= self.limit:
            return True

        # Add new request timestamp
        self.requests[client_id].append(current_time)
        return False


# Initialize the rate limiter (e.g., 10 requests per minute)
rate_limiter = InMemoryRateLimiter(limit=10, window=60)
# Resolver functions for the GraphQL schema
query = QueryType()


@query.field("users")
def resolve_users(_, info):
    request = info.context["request"]
    client_ip = request.client.host

    try:
        # Check if the request exceeds the rate limit
        if rate_limiter.is_rate_limited(client_ip):
            raise RateLimitExceededException(
                "Rate limit exceeded. Please try again later."
            )

    except RateLimitExceeded:
        # Handle rate limit exceeded response
        raise RateLimitExceeded("Rate limit exceeded. Please try again later.")

    try:
        # Fetch data from the REST API endpoint
        response = requests.get("http://localhost:5001/api/users")
        response.raise_for_status()  # Raise an error for non-2xx responses
        return response.json()
    except RequestException as e:
        # Log error or do additional handling if needed
        raise RuntimeError("Failed to fetch users data") from e


def custom_error_formatter(error, debug):
    # Handle custom error types or add specific error messages
    if isinstance(error.original_error, RateLimitExceededException):
        return {
            "message": "Rate limit exceeded. Please try again later.",
            "extensions": {"code": "RATE_LIMIT_EXCEEDED"},
        }
    elif isinstance(error.original_error, RuntimeError):
        return {
            "message": str(error.original_error),
            "extensions": {"code": "FETCH_ERROR"},
        }
    return default_format_error(error, debug)


# Create an executable schema with Ariadne
schema = make_executable_schema(type_defs, query)

# Initialize FastAPI app
app = FastAPI()


async def context_value(request: Request):
    return {"request": request}


# Add the GraphQL endpoint with GraphiQL enabled
app.add_route(
    "/graphql",
    GraphQL(
        schema,
        debug=False,
        context_value=context_value,
        error_formatter=custom_error_formatter,
    ),
)
