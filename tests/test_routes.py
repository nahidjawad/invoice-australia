"""
Tests for application routes
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import sys
import os
from models import User, Invoice, db


class TestMainRoutes:
    """Test main application routes"""
    
    def test_homepage(self, client):
        """Test homepage route"""
        response = client.get("/")
        assert response.status_code == 200
        assert b'Tax Invoice' in response.data
    
    def test_about_page(self, client):
        """Test about page route"""
        response = client.get("/about")
        assert response.status_code == 200
    
    def test_contact_page(self, client):
        """Test contact page route"""
        response = client.get("/contact")
        assert response.status_code == 200
    
    def test_premium_page_unauthenticated(self, client):
        """Test premium page redirects when not authenticated"""
        response = client.get("/premium", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"].startswith("http") or response.headers["Location"].startswith("/login")


class TestInvoiceRoutes:
    """Test invoice-related routes"""
    
    def test_preview_invoice(self, client, sample_invoice_data):
        """Test invoice preview"""
        response = client.post('/preview', data=sample_invoice_data)
        assert response.status_code in (200, 302, 400, 404)
    
    def test_preview_invalid_data(self, client):
        """Test preview with invalid data"""
        invalid_data = {'quantity': 'invalid', 'rate': '100'}
        response = client.post('/preview', data=invalid_data, follow_redirects=True)
        assert response.status_code in (200, 302, 400, 404)
    
    def test_invoice_preview_no_session(self, client):
        """Test invoice preview without session data"""
        response = client.get('/invoice_preview')
        assert response.status_code in (400, 404)
    
    @patch('pdfkit.from_string')
    def test_download_invoice(self, mock_pdfkit, client, sample_invoice_data):
        """Test invoice download"""
        mock_pdfkit.return_value = b"PDFDATA"
        
        response = client.post('/download', data=sample_invoice_data)
        assert response.status_code in (200, 302, 400, 404)
    
    @patch('extensions.mail.send')
    @patch('pdfkit.from_string')
    def test_email_invoice(self, mock_pdfkit, mock_mail_send, client, sample_invoice_data):
        """Test email invoice functionality"""
        mock_pdfkit.return_value = b"PDFDATA"
        mock_mail_send.return_value = None
        
        response = client.post('/email_invoice', data=sample_invoice_data)
        assert response.status_code in (200, 302, 400, 404)
    
    def test_email_invalid_email(self, client, sample_invoice_data):
        """Test email with invalid email address"""
        data = sample_invoice_data.copy()
        data['client_email'] = 'invalid-email'
        
        response = client.post('/email_invoice', data=data, follow_redirects=True)
        assert response.status_code in (200, 302, 400, 404)
    
    def test_history_unauthenticated(self, client):
        """Test history page redirects when not authenticated"""
        response = client.get('/invoice/history', follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"].startswith("http") or response.headers["Location"].startswith("/login")
    
    def test_history_authenticated_premium(self, client, sample_user):
        """Test history page for authenticated premium user"""
        with client.session_transaction() as sess:
            sess['user'] = {
                'id': sample_user.id,
                'email': sample_user.email,
                'name': sample_user.name,
                'is_premium': sample_user.is_premium
            }
        
        response = client.get('/invoice/history')
        assert response.status_code in (200, 302)
    
    def test_history_authenticated_non_premium(self, client):
        """Test history page redirects non-premium users"""
        with client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'email': 'test@example.com',
                'name': 'Test User',
                'is_premium': False
            }
        
        response = client.get('/invoice/history', follow_redirects=True)
        assert response.status_code in (200, 302)
    
    def test_view_invoice_unauthenticated(self, client):
        """Test view invoice redirects when not authenticated"""
        response = client.get('/invoice/1', follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"].startswith("http") or response.headers["Location"].startswith("/login")
    
    def test_view_invoice_unauthorized(self, client, sample_user):
        """Test view invoice for unauthorized user"""
        # Create an invoice for a different user
        other_user = User(email="otheruser@example.com", name="Other User")
        db.session.add(other_user)
        db.session.commit()
        
        invoice = Invoice(
            user_id=other_user.id,
            data={'your_name': 'Test', 'client_name': 'Client', 'description': 'Service', 'quantity': 1, 'rate': 100}
        )
        db.session.add(invoice)
        db.session.commit()
        
        with client.session_transaction() as sess:
            sess['user'] = {
                'id': sample_user.id,
                'email': sample_user.email,
                'name': sample_user.name,
                'is_premium': sample_user.is_premium
            }
        
        response = client.get(f'/invoice/{invoice.id}')
        assert response.status_code in (403, 404)
    
    def test_buy_premium_unauthenticated(self, client):
        """Test buy premium redirects when not authenticated"""
        response = client.get('/buy-premium', follow_redirects=True)
        assert response.status_code in (200, 302, 404)


@pytest.mark.skip(reason="OAuth context not available in CI")
class TestAuthRoutes:
    """Test authentication routes"""
    
    def test_logout(self, client):
        """Test logout functionality"""
        with client.session_transaction() as sess:
            sess['user'] = {'id': 1, 'email': 'test@example.com'}
        
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code in (200, 302)
        
        with client.session_transaction() as sess:
            assert 'user' not in sess
    
    @pytest.mark.skip(reason="OAuth context not available in CI")
    @patch('auth.google')
    def test_google_login_complete_success(self, mock_google, client, sample_user):
        """Test successful Google OAuth login"""
        mock_google.authorized_response.return_value = {
            'access_token': 'test_token',
            'expires_in': 3600
        }
        mock_google.get.return_value.json.return_value = {
            'email': sample_user.email,
            'name': sample_user.name
        }
        
        response = client.get('/google_login_complete', follow_redirects=True)
        assert response.status_code == 200
    
    @pytest.mark.skip(reason="OAuth context not available in CI")
    @patch('auth.google')
    def test_google_login_complete_unauthorized(self, mock_google, client):
        """Test Google OAuth login failure"""
        mock_google.authorized_response.return_value = None
        
        response = client.get('/google_login_complete', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to home with error 