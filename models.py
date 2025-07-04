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