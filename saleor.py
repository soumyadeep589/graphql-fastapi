from fastapi import FastAPI, HTTPException, Query
import requests

app = FastAPI()

# Set your Saleor GraphQL endpoint and API key here
SALEOR_GRAPHQL_URL = "https://store-q9m3ugvk.saleor.cloud/graphql/"
SALEOR_API_KEY = "your_api_token"


# Helper function to perform a GraphQL request to Saleor
def execute_saleor_query(query: str, variables: dict = None):
    headers = {
        # "Authorization": f"Bearer {SALEOR_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        SALEOR_GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=headers,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()
    if "errors" in data:
        raise HTTPException(status_code=400, detail=data["errors"])

    return data["data"]


# Example endpoint to fetch products from Saleor
@app.get("/products")
def get_products(
    category_id: str = Query(None, description="Filter products by category ID")
):
    query = """
    query($categoryId: ID!) {
      products(
        first: 10
        channel: "default-channel"
        filter: {categories: [$categoryId]}
      ) {
        edges {
          node {
            id
            name
            category {
              id
              name
            }
          }
        }
      }
    }
    """
    variables = {"categoryId": category_id} if category_id else {}
    data = execute_saleor_query(query, variables)
    print(data)
    return data["products"]["edges"]


# Example endpoint to get a specific product by ID
@app.get("/products/{product_id}")
def get_product_by_id(product_id: str):
    query = """
    query getProduct($id: ID!) {
      product(id: $id) {
        id
        name
        description
        pricing {
          priceRange {
            start {
              currency
              gross {
                amount
              }
            }
          }
        }
      }
    }
    """
    variables = {"id": product_id}
    data = execute_saleor_query(query, variables)
    return data["product"]
