# tests/test_app.py

import os
import sys
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app as flask_app
from unittest.mock import patch

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'Tax Invoice' in response.data  # Should show form, not invoice

def test_preview_post(client):
    form_data = {
        'your_name': 'John Doe',
        'abn': '123456789',
        'invoice_number': 'INV001',
        'date': '2024-07-01',
        'client_name': 'Client A',
        'client_email': 'client@example.com',
        'description': 'Web development services',
        'quantity': '2',
        'rate': '150',
        'include_gst': 'on'
    }
    response = client.post('/preview', data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Web development services' in response.data
    assert b'John Doe' in response.data

def test_invoice_preview_without_session(client):
    response = client.get('/invoice_preview')
    assert response.status_code == 400

def test_download_route(client):
    response = client.post(
        "/download",
        data={
            "your_name": "Test User",
            "abn": "123456789",
            "invoice_number": "INV-002",
            "date": "2025-06-25",
            "client_name": "Client Co",
            "client_email": "client@example.com",
            "description": "Web Dev",
            "quantity": "1",
            "rate": "100",
            "include_gst": "on",
            "total": "110.0"
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"

def test_email_route(client):
    with patch("app.mail.send") as mock_send:
        response = client.post(
            "/email",
            data={
                "your_name": "Jane Smith",
                "abn": "987654321",
                "invoice_number": "INV-003",
                "date": "2025-06-25",
                "client_name": "Beta Ltd",
                "client_email": "client@example.com",
                "description": "Design Work",
                "quantity": "3",
                "rate": "200",
                "include_gst": "on",
                "total": "660.0"
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Invoice emailed successfully" in response.data
        mock_send.assert_called_once()
