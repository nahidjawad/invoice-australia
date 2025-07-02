# Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd invoice-australia
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env  # If .env.example exists
   # Edit .env with your OAuth credentials
   ```

5. **Initialize database**
   ```bash
   python manage_db.py init
   ```

6. **Run the application**
   ```bash
   python run_dev.py
   ```

7. **Access the application**
   - Open your browser and go to: http://localhost:5000
   - Login with Google OAuth

## 🗄️ Database Management

### Quick Database Access
```bash
# Open interactive database shell
python manage_db.py shell

# Show database path
python manage_db.py path

# Create backup
python manage_db.py backup
```

### Common Database Commands
```sql
-- View all users
SELECT * FROM user;

-- View all invoices
SELECT * FROM invoice;

-- Set user as premium
UPDATE user SET is_premium = 1 WHERE email = 'user@example.com';

-- View recent invoices with user names
SELECT i.invoice_number, u.name, i.total_amount, i.status 
FROM invoice i 
JOIN user u ON i.user_id = u.id 
ORDER BY i.created_at DESC;
```

### Database Shell Commands
- `help` - Show available commands
- `tables` - List all tables
- `schema` - Show table schemas
- `users` - Show all users
- `invoices` - Show recent invoices
- `premium <email> <true|false>` - Set user premium status

## 🔧 Development

### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_models.py

# Run with coverage
python -m pytest --cov=.
```

### Project Structure
```
invoice-australia/
├── app.py      # Application factory
├── config.py              # Configuration settings
├── models.py              # Database models
├── routes.py              # Route handlers
├── auth.py                # Authentication logic
├── utils.py               # Utility functions
├── extensions.py          # Flask extensions
├── manage_db.py           # Database management
├── run_dev.py             # Development server
├── requirements.txt       # Python dependencies
├── docs/                  # Documentation
├── tests/                 # Test files
├── templates/             # HTML templates
├── static/                # Static files (CSS, JS, images)
└── instance/              # Instance folder (database, config)
```

## 🚨 Troubleshooting

### OAuth Issues
- Ensure OAuth credentials are set in `.env`
- Check that `OAUTHLIB_INSECURE_TRANSPORT=1` is set for development
- Verify Google OAuth app is configured for localhost:5000

### Database Issues
- Run `python manage_db.py init` to recreate database
- Check database path with `python manage_db.py path`
- Use `python manage_db.py shell` to inspect data

### Premium User Issues
- Use database shell: `python manage_db.py shell`
- Run: `premium user@example.com true`
- Or directly: `UPDATE user SET is_premium = 1 WHERE email = 'user@example.com'`

## 📚 Additional Documentation

- [Deployment Guide](DEPLOYMENT.md) - Production deployment instructions
- [Refactoring Guide](REFACTORING_GUIDE.md) - Code refactoring details
- [Fixes Summary](FIXES_SUMMARY.md) - Bug fixes and improvements 