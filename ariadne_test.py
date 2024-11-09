from fastapi import FastAPI
from ariadne import QueryType, gql, make_executable_schema
from ariadne.asgi import GraphQL
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
    # Fetch data from the REST API endpoint
    response = requests.get("http://localhost:5001/api/users")
    return response.json()

# Create an executable schema with Ariadne
schema = make_executable_schema(type_defs, query)

# Initialize FastAPI app
app = FastAPI()

# Add the GraphQL endpoint with GraphiQL enabled
app.add_route("/graphql", GraphQL(schema, debug=True))
