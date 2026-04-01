"""
Tests for activities endpoints.
Covers activity listing, signup functionality, validation, and business logic.
"""
import pytest
from src.app import activities


class TestGetActivities:
    """Tests for retrieving activities list."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all activities are present
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Verify activity structure
        assert "description" in data["Chess Club"]
        assert "schedule" in data["Chess Club"]
        assert "max_participants" in data["Chess Club"]
        assert "participants" in data["Chess Club"]

    def test_get_activities_contains_correct_data(self, client):
        """Test that activity data is correct."""
        response = client.get("/activities")
        data = response.json()
        
        chess = data["Chess Club"]
        assert chess["max_participants"] == 12
        assert "michael@mergington.edu" in chess["participants"]
        assert "daniel@mergington.edu" in chess["participants"]


class TestSignupForActivity:
    """Tests for signing up for activities."""

    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity."""
        email = "new_student@mergington.edu"
        activity_name = "Chess Club"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        assert response.status_code == 200
        assert response.json() == {
            "message": f"Signed up {email} for {activity_name}"
        }
        assert email in activities[activity_name]["participants"]

    def test_signup_for_activity_not_found(self, client):
        """Test signup for nonexistent activity returns 404."""
        response = client.post(
            "/activities/NonExistentClub/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_multiple_students_same_activity(self, client):
        """Test multiple students can sign up for the same activity."""
        activity = "Programming Class"
        email1 = "alice@mergington.edu"
        email2 = "bob@mergington.edu"

        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email2}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email1 in activities[activity]["participants"]
        assert email2 in activities[activity]["participants"]


class TestSignupValidation:
    """Tests for signup parameter validation and edge cases."""

    @pytest.mark.parametrize("email", [
        "student.name@mergington.edu",
        "student+tag@mergington.edu",
        "123@mergington.edu",
    ])
    def test_signup_with_valid_email_formats(self, client, email):
        """Test signup with various valid email formats."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in activities["Chess Club"]["participants"]

    def test_signup_with_empty_email(self, client):
        """Test signup with empty email parameter."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ""}
        )
        # Empty string is still technically valid in current implementation
        # but should be in participants list
        assert response.status_code == 200
        assert "" in activities["Chess Club"]["participants"]

    def test_signup_preserves_existing_participants(self, client):
        """Test that new signup doesn't remove existing participants."""
        activity = "Gym Class"
        original_participants = activities[activity]["participants"].copy()
        
        new_email = "new_participant@mergington.edu"
        client.post(
            f"/activities/{activity}/signup",
            params={"email": new_email}
        )

        # Original participants should still be present
        for original_email in original_participants:
            assert original_email in activities[activity]["participants"]
        
        # New participant should be added
        assert new_email in activities[activity]["participants"]


class TestSignupCapacityAndDuplicates:
    """Tests for business logic: capacity limits and duplicate signups."""

    def test_signup_duplicate_email_not_prevented(self, client):
        """
        Test current behavior: duplicate signups are not prevented.
        This may be intentional or a bug to fix.
        """
        activity = "Chess Club"
        email = "duplicate_test@mergington.edu"
        
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Both requests succeed in current implementation
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Email appears twice in participants list
        count = activities[activity]["participants"].count(email)
        assert count == 2

    def test_capacity_not_enforced(self, client):
        """
        Test current behavior: capacity limits are not enforced.
        Chess Club has max_participants=12 but allows unlimited signups.
        This may be intentional or a bug to fix.
        """
        activity = "Chess Club"
        max_capacity = activities[activity]["max_participants"]
        
        # Sign up more students than max capacity
        for i in range(max_capacity + 5):
            email = f"overflow_student_{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # All signups were accepted despite exceeding capacity
        assert len(activities[activity]["participants"]) > max_capacity

    def test_capacity_check_should_be_implemented(self, client):
        """
        NOTE: This test documents that capacity checking should be implemented.
        Current implementation allows unlimited capacity.
        
        TODO: Implement capacity validation in signup endpoint.
        """
        activity = "Chess Club"
        max_capacity = activities[activity]["max_participants"]
        current_count = len(activities[activity]["participants"])
        
        # Fill up to capacity
        for i in range(max_capacity - current_count):
            email = f"capacity_test_{i}@mergington.edu"
            client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
        
        # Verify at capacity
        assert len(activities[activity]["participants"]) == max_capacity
        
        # Try to signup when at capacity (should fail in future implementation)
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "overflow@mergington.edu"}
        )
        
        # Currently succeeds - should be 400 or 409 when capacity is enforced
        assert response.status_code == 200  # This will need to change


class TestActivityNameVariations:
    """Tests for activity name matching and case sensitivity."""

    def test_activity_name_case_sensitive(self, client):
        """Test that activity name lookup is case-sensitive."""
        response = client.post(
            "/activities/chess club/signup",  # lowercase
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404

    def test_activity_name_with_extra_whitespace(self, client):
        """Test that activity names must match exactly (including whitespace)."""
        response = client.post(
            "/activities/Chess Club /signup",  # trailing space
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404

    def test_typo_in_activity_name(self, client):
        """Test that typos in activity names are not corrected."""
        response = client.post(
            "/activities/Ches Club/signup",  # typo: "Ches" instead of "Chess"
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
