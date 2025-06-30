# Invoice Australia

A modern, Flask-based invoice generation application with Google OAuth authentication and premium features.

## 🚀 Features

- **Invoice Generation**: Create professional PDF invoices
- **Google OAuth**: Secure authentication with Google accounts
- **Premium Features**: Invoice history and management for premium users
- **Email Integration**: Send invoices directly to clients
- **Modern UI**: Clean, responsive Bootstrap-based interface

## 📁 Project Structure

```
invoice-australia/
├── app_refactored.py      # Main application factory
├── config.py              # Configuration settings
├── extensions.py          # Flask extensions (SQLAlchemy, Mail)
├── models.py              # Database models (User, Invoice)
├── routes.py              # Application routes and views
├── auth.py                # Authentication and OAuth logic
├── utils.py               # Utility functions and helpers
├── run_dev.py             # Development server runner
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project metadata
├── setup.cfg              # Pytest configuration
├── .env                   # Environment variables (create from .env.template)
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── templates/             # Jinja2 HTML templates
├── static/                # Static files (CSS, JS, images)
├── instance/              # Instance-specific files (database)
├── tests/                 # Test suite
└── output/                # Generated PDF invoices
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8+
- Google OAuth credentials

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
   cp .env.template .env
   # Edit .env with your actual values
   ```

5. **Run the application**
   ```bash
   python run_dev.py
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Email Configuration
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Security
SECRET_KEY=your-secret-key

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

# Application Environment
FLASK_ENV=development
OAUTHLIB_INSECURE_TRANSPORT=1
OAUTHLIB_RELAX_TOKEN_SCOPE=1
```

## 🧪 Testing

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=.
```

## 📝 Usage

1. **Access the application** at `http://localhost:5000`
2. **Sign in** with your Google account
3. **Create invoices** using the form
4. **Download or email** invoices to clients
5. **View history** (premium feature)

## 🏗️ Architecture

- **Flask Blueprints**: Modular route organization
- **SQLAlchemy**: Database ORM with SQLite
- **Flask-Mail**: Email functionality
- **Google OAuth**: Authentication system
- **Bootstrap**: Frontend framework

## 🔒 Security Features

- OAuth 2.0 authentication
- CSRF protection
- Input validation
- Secure session management
- Environment variable configuration

## 📊 Database Schema

### Users Table
- `id`: Primary key
- `email`: User email (unique)
- `name`: User display name
- `is_premium`: Premium status
- `created_at`: Account creation timestamp

### Invoices Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `data`: JSON invoice data
- `created_at`: Invoice creation timestamp

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support, please open an issue in the GitHub repository.

