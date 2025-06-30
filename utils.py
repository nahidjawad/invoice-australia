import re
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from flask import session
import pdfkit

class InvoiceProcessor:
    """Handles invoice data processing and calculations"""
    
    @staticmethod
    def process_form_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate form data"""
        processed_data = data.copy()
        
        # Handle GST inclusion
        processed_data['include_gst'] = 'include_gst' in data
        
        # Format date
        date_str = data.get('date', '')
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                processed_data['formatted_date'] = date_obj.strftime('%d/%m/%Y')
                processed_data['date'] = date_str
            except ValueError:
                processed_data['formatted_date'] = date_str
        
        # Calculate totals
        try:
            qty = int(data['quantity'])
            rate = float(data['rate'])
            total = qty * rate
            
            if processed_data['include_gst']:
                total *= 1.10
                
            processed_data['total'] = round(total, 2)
            processed_data['rate'] = rate
            processed_data['quantity'] = qty
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid quantity or rate: {e}")
        
        return processed_data
    
    @staticmethod
    def generate_filename(your_name: str) -> str:
        """Generate a safe filename for the PDF"""
        name_slug = re.sub(r'\W+', '', your_name).lower()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        return f"{name_slug}-{timestamp}.pdf"
    
    @staticmethod
    def create_pdf(html_content: str, filename: str) -> str:
        """Create PDF from HTML content"""
        os.makedirs('output', exist_ok=True)
        pdf_path = os.path.join('output', filename)
        
        try:
            pdfkit.from_string(html_content, pdf_path)
            return pdf_path
        except Exception as e:
            raise RuntimeError(f"Failed to create PDF: {e}")

class SessionManager:
    """Manages session data"""
    
    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """Get current user from session"""
        return session.get("user")
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return "user" in session
    
    @staticmethod
    def is_premium_user() -> bool:
        """Check if current user has premium access"""
        user = session.get("user")
        return user and user.get("is_premium", False)
    
    @staticmethod
    def store_invoice_data(data: Dict[str, Any]) -> None:
        """Store invoice data in session for preview/edit"""
        session["last_invoice_data"] = data
    
    @staticmethod
    def get_invoice_data() -> Optional[Dict[str, Any]]:
        """Get stored invoice data from session"""
        return session.get("last_invoice_data")

class EmailValidator:
    """Email validation utilities"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email address"""
        return email.strip().lower() 