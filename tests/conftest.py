"""
Pytest configuration and shared fixtures for Invoice Australia tests
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
import uuid
import os

from app_refactored import create_app
from models import db, User, Invoice
from extensions import init_extensions

os.makedirs('instance', exist_ok=True)


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    print("TEST DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    return app


@pytest.fixture(scope='function')
def client(app):
    """Create test client with database context"""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        name="Test User",
        is_premium=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing"""
    return {
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


@pytest.fixture
def sample_invoice_json():
    """Sample invoice data as JSON string"""
    data = {
        'your_name': 'John Doe',
        'abn': '123456789',
        'invoice_number': 'INV001',
        'date': '2024-07-01',
        'client_name': 'Client A',
        'client_email': 'client@example.com',
        'description': 'Web development services',
        'quantity': 2,
        'rate': 150.0,
        'include_gst': True,
        'total': 330.0,
        'formatted_date': '01/07/2024'
    }
    return json.dumps(data)
