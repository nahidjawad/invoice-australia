from sqlalchemy.dialects.sqlite import JSON  # Add this at the top with other imports

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    invoices = db.relationship('Invoice', backref='user', lazy=True)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(JSON, nullable=False)  # <-- change from Text to JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
