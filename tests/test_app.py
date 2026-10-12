from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY_NAME = "Chess Club"
SIGNUP_URL = "/activities/Chess%20Club/signup"


@pytest.fixture
def activity_data(monkeypatch):
    isolated_activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture
def client(activity_data):
    return TestClient(app_module.app)


def test_get_activities_returns_activity_data(client, activity_data):
    # Arrange
    expected_activities = activity_data

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activity_data):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    response = client.post(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}"}
    assert email in activity_data[ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_participant(client, activity_data):
    # Arrange
    email = activity_data[ACTIVITY_NAME]["participants"][0]
    original_participants = activity_data[ACTIVITY_NAME]["participants"].copy()

    # Act
    response = client.post(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activity_data[ACTIVITY_NAME]["participants"] == original_participants


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    response = client.post("/activities/Unknown%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client, activity_data):
    # Arrange
    email = activity_data[ACTIVITY_NAME]["participants"][0]

    # Act
    response = client.delete(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {ACTIVITY_NAME}"}
    assert email not in activity_data[ACTIVITY_NAME]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.delete("/activities/Unknown%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_nonparticipant(client, activity_data):
    # Arrange
    email = "not.signed.up@mergington.edu"
    original_participants = activity_data[ACTIVITY_NAME]["participants"].copy()

    # Act
    response = client.delete(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activity_data[ACTIVITY_NAME]["participants"] == original_participants