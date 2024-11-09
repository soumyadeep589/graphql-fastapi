from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from graphene import ObjectType, String, ID, List, Schema
# import requests
import graphene

app = FastAPI()

# Define the User type for GraphQL
class User(graphene.ObjectType):
    id = ID()
    name = String()
    email = String()

# Define the Query class with a `users` field
class Query(ObjectType):
    users = List(User)

    # Resolver for the `users` query
    def resolve_users(root, info):
        # Fetch data from the REST API endpoint
        # response = requests.get("http://localhost:5001/api/users")
        # data = response.json()
        # # Map the JSON data to User objects
        # return [User(id=user["id"], name=user["name"], email=user["email"]) for user in data]
        return [User(id=1, name="first", email="first_email"),
                User(id=1, name="second", email="second_email"),
                User(id=1, name="third", email="third_email")
                
                ]

# Create the GraphQL schema
schema = Schema(query=Query)

# Define the GraphQL endpoint in FastAPI
@app.post("/graphql")
async def graphql_endpoint(request: Request):
    # Parse the incoming request
    body = await request.json()
    query = body.get("query")
    # Execute the GraphQL query
    result = schema.execute(query)
    # Return the result as a JSON response
    return JSONResponse(result.data)
