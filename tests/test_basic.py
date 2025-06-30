"""
Basic tests to verify the application works
"""

import pytest
import os
import sys

def test_app_import():
    """Test that the refactored app can be imported"""
    try:
        from app_refactored import create_app
        assert create_app is not None
    except ImportError as e:
        pytest.fail(f"Failed to import create_app: {e}")

def test_app_creation():
    """Test that the app can be created"""
    try:
        from app_refactored import create_app
        app = create_app('testing')
        assert app is not None
        assert app.config['TESTING'] is True
    except Exception as e:
        pytest.fail(f"Failed to create app: {e}")

def test_config_import():
    """Test that config can be imported"""
    try:
        from config import DevelopmentConfig, TestingConfig, ProductionConfig
        assert DevelopmentConfig is not None
        assert TestingConfig is not None
        assert ProductionConfig is not None
    except ImportError as e:
        pytest.fail(f"Failed to import config: {e}")

def test_models_import():
    """Test that models can be imported"""
    try:
        from models import User, Invoice, db
        assert User is not None
        assert Invoice is not None
        assert db is not None
    except ImportError as e:
        pytest.fail(f"Failed to import models: {e}")

def test_utils_import():
    """Test that utils can be imported"""
    try:
        from utils import InvoiceProcessor, SessionManager, EmailValidator
        assert InvoiceProcessor is not None
        assert SessionManager is not None
        assert EmailValidator is not None
    except ImportError as e:
        pytest.fail(f"Failed to import utils: {e}")

def test_extensions_import():
    """Test that extensions can be imported"""
    try:
        from extensions import db, mail, init_extensions
        assert db is not None
        assert mail is not None
        assert init_extensions is not None
    except ImportError as e:
        pytest.fail(f"Failed to import extensions: {e}")

def test_basic_invoice_processing():
    """Test basic invoice processing functionality"""
    try:
        from utils import InvoiceProcessor
        
        # Test data
        test_data = {
            'your_name': 'John Doe',
            'client_name': 'Client A',
            'description': 'Test service',
            'quantity': '2',
            'rate': '100',
            'include_gst': 'on'
        }
        
        # Process the data
        result = InvoiceProcessor.process_form_data(test_data)
        
        # Verify results
        assert result['include_gst'] is True
        assert result['quantity'] == 2
        assert result['rate'] == 100.0
        assert result['total'] == 220.0  # 2 * 100 * 1.1 (GST)
        
    except Exception as e:
        pytest.fail(f"Failed to process invoice data: {e}")

def test_email_validation():
    """Test email validation functionality"""
    try:
        from utils import EmailValidator
        
        # Test valid emails
        assert EmailValidator.is_valid_email("test@example.com") is True
        assert EmailValidator.is_valid_email("user.name@domain.co.uk") is True
        
        # Test invalid emails
        assert EmailValidator.is_valid_email("invalid-email") is False
        assert EmailValidator.is_valid_email("@domain.com") is False
        assert EmailValidator.is_valid_email("") is False
        
    except Exception as e:
        pytest.fail(f"Failed to validate emails: {e}") 