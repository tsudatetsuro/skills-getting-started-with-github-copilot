from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


initial_activities = deepcopy(activities)
client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    yield
    activities.clear()
    activities.update(deepcopy(initial_activities))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    response_activities = response.json()
    assert set(response_activities) == set(initial_activities)
    assert response_activities["Chess Club"] == initial_activities["Chess Club"]


def test_signup_adds_new_participant():
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new.student@mergington.edu for Chess Club"
    }
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant():
    email = "michael@mergington.edu"
    original_participants = activities["Chess Club"]["participants"].copy()

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Student is already signed up for this activity"
    )
    assert activities["Chess Club"]["participants"] == original_participants


def test_signup_requires_email():
    response = client.post("/activities/Chess Club/signup")

    assert response.status_code == 422


def test_delete_removes_participant():
    email = "michael@mergington.edu"

    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }
    assert email not in activities["Chess Club"]["participants"]
    assert email not in client.get("/activities").json()["Chess Club"]["participants"]


def test_delete_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_rejects_unknown_participant():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "not.registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student is not signed up for this activity"
    )


def test_delete_requires_email():
    response = client.delete("/activities/Chess Club/signup")

    assert response.status_code == 422