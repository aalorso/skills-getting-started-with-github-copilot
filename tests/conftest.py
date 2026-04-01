"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Reset activities to their initial state before each test.
    This ensures tests don't interfere with each other due to state mutations.
    """
    # Store original state
    original_state = {
        name: {
            "description": data["description"],
            "schedule": data["schedule"],
            "max_participants": data["max_participants"],
            "participants": data["participants"].copy()
        }
        for name, data in activities.items()
    }

    yield

    # Restore original state after test
    for name, original_data in original_state.items():
        activities[name]["participants"] = original_data["participants"].copy()


@pytest.fixture(autouse=True)
def ensure_clean_state(reset_activities):
    """Automatically reset activities state for each test."""
    pass
