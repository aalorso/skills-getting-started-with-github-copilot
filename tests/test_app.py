from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


def test_root_redirect():
    response = client.get("/")
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    assert response.json() == activities


def test_signup_for_activity_success():
    email = "new_student@mergington.edu"
    activity_name = "Chess Club"
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]

    # Cleanup state so tests remain idempotent
    activities[activity_name]["participants"].remove(email)


def test_signup_for_activity_not_found():
    response = client.post("/activities/NonExistent/signup", params={"email": "x@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_static_index_available():
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
