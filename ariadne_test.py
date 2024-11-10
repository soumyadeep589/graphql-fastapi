from fastapi import FastAPI
from ariadne import QueryType, gql, make_executable_schema, format_error as default_format_error
from ariadne.asgi import GraphQL
from requests.exceptions import RequestException
import requests


# Define GraphQL schema in SDL (Schema Definition Language)
type_defs = gql("""
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
""")

# Resolver functions for the GraphQL schema
query = QueryType()

@query.field("users")
def resolve_users(*_):
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
    if isinstance(error.original_error, RuntimeError):
        return {
            "message": str(error.original_error),
            "extensions": {"code": "FETCH_ERROR"}
        }
    # Fallback to default formatting
    return default_format_error(error, debug)

# Create an executable schema with Ariadne
schema = make_executable_schema(type_defs, query)

# Initialize FastAPI app
app = FastAPI()

# Add the GraphQL endpoint with GraphiQL enabled
app.add_route("/graphql", GraphQL(schema, debug=True))
