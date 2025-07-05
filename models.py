from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import validates
import re
import json

# Import db from extensions to avoid duplicate instances
from extensions import db

# Association table for many-to-many relationship
user_company = db.Table('user_company',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('company_id', db.Integer, db.ForeignKey('companies.id'), primary_key=True)
)

class User(db.Model):
    """User model for authentication and premium features"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invoices = db.relationship("Invoice", backref="user", lazy=True, cascade="all, delete-orphan")
    companies = db.relationship('Company', secondary=user_company, back_populates='users')
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        if not email or '@' not in email:
            raise ValueError('Invalid email address')
        return email.lower()
    
    def __repr__(self):
        return f'<User {self.email}>'

class Invoice(db.Model):
    """Invoice model for storing invoice data"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data = db.Column(db.Text, nullable=False)  # Store as text to handle existing JSON strings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Unpaid')
    
    @property
    def invoice_data(self):
        """Convert stored JSON string to dictionary"""
        if isinstance(self.data, dict):
            return self.data
        try:
            return json.loads(self.data) if self.data else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @validates('data')
    def validate_data(self, key, data):
        """Validate invoice data structure"""
        # Convert to dict if it's a string
        if isinstance(data, str):
            try:
                data_dict = json.loads(data)
            except json.JSONDecodeError:
                raise ValueError('Invalid JSON data')
        else:
            data_dict = data
            
        required_fields = ['your_name', 'client_name', 'description', 'quantity', 'rate']
        for field in required_fields:
            if field not in data_dict:
                raise ValueError(f'Missing required field: {field}')
        
        # Store as JSON string
        return json.dumps(data_dict) if isinstance(data, dict) else data
    
    def __repr__(self):
        return f'<Invoice {self.id} for user {self.user_id}>'

class AdvancedInvoiceItem(db.Model):
    """Individual line items for advanced invoices"""
    __tablename__ = 'advanced_invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    advanced_invoice_id = db.Column(db.Integer, db.ForeignKey('advanced_invoices.id'), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    rate = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdvancedInvoiceItem {self.description} - ${self.total}>'

class AdvancedInvoice(db.Model):
    """Advanced invoice model with multiple items, GST support, and company selection"""
    __tablename__ = 'advanced_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Invoice details
    invoice_number = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    include_gst = db.Column(db.Boolean, default=False)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    gst_amount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Unpaid')
    
    # Sender details (either personal or company)
    use_company = db.Column(db.Boolean, default=False)  # True = use company, False = use personal
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    
    # Personal details (used when use_company = False)
    your_name = db.Column(db.String(120), nullable=True)
    abn = db.Column(db.String(20), nullable=True)
    
    # Client details
    client_name = db.Column(db.String(120), nullable=False)
    client_email = db.Column(db.String(120), nullable=False)
    
    # Relationships
    items = db.relationship("AdvancedInvoiceItem", backref="advanced_invoice", lazy=True, cascade="all, delete-orphan")
    user = db.relationship("User", backref="advanced_invoices")
    company = db.relationship("Company", backref="advanced_invoices")
    
    def calculate_totals(self):
        """Calculate subtotal, GST, and total amounts"""
        self.subtotal = sum(item.total for item in self.items)
        self.gst_amount = self.subtotal * 0.1 if self.include_gst else 0.0
        self.total = self.subtotal + self.gst_amount
    
    def get_sender_details(self):
        """Get sender details (either company or personal)"""
        if self.use_company and self.company:
            return {
                'name': self.company.company_name,
                'abn': self.company.abn,
                'address': self.company.address,
                'phone': self.company.phone,
                'email': self.company.email,
                'logo_path': self.company.logo_path
            }
        else:
            return {
                'name': self.your_name,
                'abn': self.abn,
                'address': None,
                'phone': None,
                'email': None,
                'logo_path': None
            }
    
    def __repr__(self):
        return f'<AdvancedInvoice {self.id} for user {self.user_id}>'

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), nullable=False)
    abn = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    payment_details = db.Column(db.Text, nullable=True)
    logo_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    users = db.relationship('User', secondary=user_company, back_populates='companies')