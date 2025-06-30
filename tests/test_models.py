"""
Tests for database models
"""

import pytest
import json
from datetime import datetime

from models import User, Invoice, db


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, app):
        """Test creating a new user"""
        with app.app_context():
            db.create_all()
            
            user = User(
                email="test_user_creation@example.com",
                name="Test User",
                is_premium=True
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.email == "test_user_creation@example.com"
            assert user.name == "Test User"
            assert user.is_premium is True
            assert user.created_at is not None
    
    def test_user_email_validation(self, app):
        """Test user email validation"""
        with app.app_context():
            db.create_all()
            
            # Test valid email
            user = User(
                email="valid@example.com",
                name="Test User"
            )
            db.session.add(user)
            db.session.commit()
            assert user.email == "valid@example.com"
            
            # Test invalid email
            with pytest.raises(ValueError, match="Invalid email address"):
                user2 = User(
                    email="invalid-email",
                    name="Test User"
                )
    
    def test_user_repr(self, app):
        """Test user string representation"""
        with app.app_context():
            db.create_all()
            
            user = User(
                email="test_user_repr@example.com",
                name="Test User"
            )
            db.session.add(user)
            db.session.commit()
            
            assert str(user) == "<User test_user_repr@example.com>"


class TestInvoiceModel:
    """Test Invoice model functionality"""
    
    def test_invoice_creation(self, app, sample_user):
        """Test creating a new invoice"""
        with app.app_context():
            db.create_all()
            
            invoice_data = {
                'your_name': 'John Doe',
                'client_name': 'Client A',
                'description': 'Test service',
                'quantity': 2,
                'rate': 100.0,
                'total': 220.0
            }
            
            invoice = Invoice(
                user_id=sample_user.id,
                data=invoice_data
            )
            db.session.add(invoice)
            db.session.commit()
            
            assert invoice.id is not None
            assert invoice.user_id == sample_user.id
            assert invoice.created_at is not None
    
    def test_invoice_data_validation(self, app, sample_user):
        """Test invoice data validation"""
        with app.app_context():
            db.create_all()
            
            # Test valid data
            valid_data = {
                'your_name': 'John Doe',
                'client_name': 'Client A',
                'description': 'Test service',
                'quantity': 2,
                'rate': 100.0
            }
            
            invoice = Invoice(
                user_id=sample_user.id,
                data=valid_data
            )
            db.session.add(invoice)
            db.session.commit()
            
            # Test invalid data (missing required fields)
            invalid_data = {
                'your_name': 'John Doe',
                # Missing client_name, description, quantity, rate
            }
            
            with pytest.raises(ValueError, match="Missing required field"):
                invoice2 = Invoice(
                    user_id=sample_user.id,
                    data=invalid_data
                )
    
    def test_invoice_data_property(self, app, sample_user, sample_invoice_json):
        """Test invoice_data property for JSON string conversion"""
        with app.app_context():
            db.create_all()
            
            invoice = Invoice(
                user_id=sample_user.id,
                data=sample_invoice_json
            )
            db.session.add(invoice)
            db.session.commit()
            
            # Test that invoice_data property works
            data = invoice.invoice_data
            assert isinstance(data, dict)
            assert data['your_name'] == 'John Doe'
            assert data['client_name'] == 'Client A'
            assert data['total'] == 330.0
    
    def test_invoice_repr(self, app, sample_user):
        """Test invoice string representation"""
        with app.app_context():
            db.create_all()
            
            invoice = Invoice(
                user_id=sample_user.id,
                data={'your_name': 'Test', 'client_name': 'Client', 'description': 'Service', 'quantity': 1, 'rate': 100}
            )
            db.session.add(invoice)
            db.session.commit()
            
            assert str(invoice) == f"<Invoice {invoice.id} for user {sample_user.id}>"


class TestModelRelationships:
    """Test model relationships"""
    
    def test_user_invoices_relationship(self, app):
        """Test user-invoice relationship"""
        with app.app_context():
            db.create_all()
            
            user = User(
                email="test_relationship@example.com",
                name="Test User"
            )
            db.session.add(user)
            db.session.commit()
            
            # Create invoices for user
            invoice1 = Invoice(
                user_id=user.id,
                data={'your_name': 'Test', 'client_name': 'Client1', 'description': 'Service1', 'quantity': 1, 'rate': 100}
            )
            invoice2 = Invoice(
                user_id=user.id,
                data={'your_name': 'Test', 'client_name': 'Client2', 'description': 'Service2', 'quantity': 2, 'rate': 200}
            )
            db.session.add_all([invoice1, invoice2])
            db.session.commit()
            
            # Test relationship
            assert len(user.invoices) == 2
            assert invoice1 in user.invoices
            assert invoice2 in user.invoices
            assert user.invoices[0].user == user 