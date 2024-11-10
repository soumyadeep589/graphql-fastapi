import pytest
from fastapi.testclient import TestClient
from time import sleep
from server import app

# Initialize the TestClient for FastAPI
client = TestClient(app)

# Test for the successful response when rate limit is not exceeded
def test_users_success():
    # Reset rate limiter state for this test case by adding sleep
    sleep(1)  # Small delay to simulate a fresh request window

    response = client.post(
        "/graphql",
        json={
            "query": "{ users { id name email address { street city zipcode } } }"
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "users" in data
    assert isinstance(data["users"], list)

# Test for error when failing to fetch user data from the external API
def test_fetch_data_failure():
    # Simulate an API failure by using an invalid URL or making the API down
    with pytest.raises(Exception):
        response = client.post(
            "/graphql",
            json={
                "query": "{ users { id name email address { street city zipcode } } }"
            },
        )
        assert response.status_code == 500
        assert "Failed to fetch users data" in response.json()["errors"][0]["message"]


def test_rate_limiting():
    # Making 10 requests to trigger the rate limit
    for _ in range(10):
        response = client.post(
            "/graphql",
            json={
                "query": "{ users { id name email address { street city zipcode } } }"
            },
        )
        assert response.status_code == 200

    # 11th request should be rate-limited
    response = client.post(
        "/graphql",
        json={
            "query": "{ users { id name email address { street city zipcode } } }"
        },
    )
    assert response.status_code == 200
    assert "Rate limit exceeded" in response.json()["errors"][0]["message"]