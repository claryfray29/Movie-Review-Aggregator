import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from database import Base, get_db
from main import app
import os

from dotenv import load_dotenv

load_dotenv()

# 1. Grab the exact live DB URL configuration string from database.py context
PROD_DB_URL = os.getenv("DB_URL")

if not PROD_DB_URL:
    raise RuntimeError("DB_URL is missing from your environment variables (.env file).")

# If the connection string points to 'movieAggregator', we redirect it to 'movieAggregator_test'
if "movieAggregator_test" not in PROD_DB_URL:
    # Swap out the target database schema name safely at the end of the connection string
    MYSQL_TEST_DB_URL = PROD_DB_URL.replace("/movieAggregator", "/movieAggregator_test")
else:
    MYSQL_TEST_DB_URL = PROD_DB_URL

engine = create_engine(MYSQL_TEST_DB_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the database dependency to route transactions through the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Instantiate the TestClient (our fast simulated internal browser)
client = TestClient(app)

# Clean and rebuild our exact SQL structure before running the test cases
@pytest.fixture(autouse=True, scope="module")
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


#USER REGISTRATION & LOGIN TEST CASES

def test_register_user_success():
    """Test successful user registration."""
    response = client.post("/users/", json={"user_name": "clary", "user_login": "shadowhunter"})
    assert response.status_code == 200
    assert response.json()["user_name"] == "clary"

def test_register_user_duplicate_username():
    """Edge Case: Ensure registering an existing username triggers a 400 bad request error."""
    # First creation call
    client.post("/users/", json={"user_name": "jace", "user_login": "herondale"})
    
    # Duplicate call must be caught by user validation rules
    response = client.post("/users/", json={"user_name": "jace", "user_login": "differentpass"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists"

def test_login_success():
    """Test standard application login returns a valid Bearer token string layout."""
    response = client.post("/login", data={"username": "clary", "password": "shadowhunter"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_credentials():
    """Edge Case: Confirm login blocks requests matching wrong access combinations."""
    response = client.post("/login", data={"username": "clary", "password": "wrong_password"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect credentials"


#MOVIE ENGINE & SEARCH TEST CASES

def test_search_movie_missing_title_parameter():
    """Edge Case: Confirm sending a search query with an empty movie name parameter defaults to a 400 validation warning."""
    response = client.get("/movies/search?title=")
    assert response.status_code == 400
    assert response.json()["detail"] == "Movie title required."


#REVIEWS & AUTH PERMISSIONS TEST CASES

def test_post_review_unauthorized():
    """Edge Case: Ensure unauthenticated users are blocked from creating movie reviews."""
    review_payload = {
        "movie_name": "Inception",
        "rating": 5,
        "comment": "Mind bending masterpiece."
    }
    response = client.post("/movies/reviews/", json=review_payload)
    # FastAPI security triggers an automatic 401 Unauthorized block due to lack of token headers
    assert response.status_code == 401