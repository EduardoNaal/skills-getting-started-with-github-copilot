"""
Test suite for Mergington High School API (AAA pattern)
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
import sys
from pathlib import Path

# Arrange: Add src to path to import app
sys.path.insert(0, str(Path(__file__).parent / "../src"))
from src.app import app, activities

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def reset_activities():
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(original))

# --- ROOT ENDPOINT ---
def test_root_redirects_to_static(client):
    # Arrange
    # Act
    response = client.get("/", follow_redirects=False)
    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"

# --- ACTIVITIES LIST ---
def test_get_activities_returns_all(client, reset_activities):
    # Arrange
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data

def test_activity_structure(client, reset_activities):
    # Arrange
    # Act
    response = client.get("/activities")
    # Assert
    for activity in response.json().values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
        assert isinstance(activity["max_participants"], int)

def test_initial_participants(client, reset_activities):
    # Arrange
    # Act
    response = client.get("/activities")
    # Assert
    chess = response.json()["Chess Club"]
    assert "michael@mergington.edu" in chess["participants"]
    assert "daniel@mergington.edu" in chess["participants"]

# --- SIGNUP ---
def test_signup_success(client, reset_activities):
    # Arrange
    email = "nuevo@mergington.edu"
    activity = "Chess Club"
    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")
    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    # Confirm in list
    data = client.get("/activities").json()
    assert email in data[activity]["participants"]

def test_signup_nonexistent_activity(client, reset_activities):
    # Arrange
    # Act
    response = client.post("/activities/NoExiste/signup?email=alguien@mergington.edu")
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]

def test_signup_duplicate(client, reset_activities):
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"
    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")
    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]

def test_signup_multiple_students(client, reset_activities):
    # Arrange
    emails = ["uno@mergington.edu", "dos@mergington.edu"]
    activity = "Chess Club"
    # Act
    for email in emails:
        resp = client.post(f"/activities/{activity}/signup?email={email}")
        assert resp.status_code == 200
    # Assert
    data = client.get("/activities").json()
    for email in emails:
        assert email in data[activity]["participants"]

def test_signup_same_student_multiple_activities(client, reset_activities):
    # Arrange
    email = "multi@mergington.edu"
    acts = ["Chess Club", "Programming Class"]
    # Act
    for act in acts:
        resp = client.post(f"/activities/{act}/signup?email={email}")
        assert resp.status_code == 200
    # Assert
    data = client.get("/activities").json()
    for act in acts:
        assert email in data[act]["participants"]

# --- REMOVE PARTICIPANT ---
def test_remove_success(client, reset_activities):
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"
    # Act
    response = client.delete(f"/activities/{activity}/participants?email={email}")
    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    # Confirm removal
    data = client.get("/activities").json()
    assert email not in data[activity]["participants"]

def test_remove_nonexistent_activity(client, reset_activities):
    # Arrange
    # Act
    response = client.delete("/activities/NoExiste/participants?email=alguien@mergington.edu")
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]

def test_remove_nonexistent_participant(client, reset_activities):
    # Arrange
    email = "noesta@mergington.edu"
    activity = "Chess Club"
    # Act
    response = client.delete(f"/activities/{activity}/participants?email={email}")
    # Assert
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]

def test_remove_and_rejoin(client, reset_activities):
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"
    # Act
    client.delete(f"/activities/{activity}/participants?email={email}")
    response = client.post(f"/activities/{activity}/signup?email={email}")
    # Assert
    assert response.status_code == 200
    data = client.get("/activities").json()
    assert email in data[activity]["participants"]
