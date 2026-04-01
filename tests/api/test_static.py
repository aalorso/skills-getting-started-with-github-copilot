"""
Tests for static file serving and redirects.
"""
import pytest


class TestRootRedirect:
    """Tests for root path redirects."""

    def test_root_redirect(self, client):
        """Test that root path redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestStaticFiles:
    """Tests for static file serving."""

    @pytest.mark.parametrize("filepath,content_type", [
        ("/static/index.html", "text/html"),
        ("/static/styles.css", "text/css"),
        ("/static/app.js", "text/javascript"),
    ])
    def test_static_files_available(self, client, filepath, content_type):
        """Test that all static files are served with correct content types."""
        response = client.get(filepath)
        assert response.status_code == 200
        assert content_type in response.headers.get("content-type", "")

    def test_nonexistent_static_file(self, client):
        """Test that nonexistent static files return 404."""
        response = client.get("/static/nonexistent.txt")
        assert response.status_code == 404
