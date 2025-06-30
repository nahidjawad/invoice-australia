# 🚀 Deployment Guide: Invoice Australia

This guide will help you deploy the Invoice Australia Flask app to production.

---

## 1. Prerequisites
- Python 3.8+
- A Linux server (Ubuntu recommended)
- Google OAuth credentials
- SMTP credentials for email
- [Optional] Nginx for reverse proxy

## 2. Environment Variables
Create a `.env` file in your project root (never commit this to git):

```
SECRET_KEY=your-production-secret-key
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
FLASK_ENV=production
DATABASE_URL=sqlite:///instance/invoices.db
```

## 3. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Database Setup
```bash
mkdir -p instance
python
>>> from app_refactored import create_app
>>> app = create_app('production')
>>> from extensions import db
>>> with app.app_context():
...     db.create_all()
... 
```

## 5. Run with Gunicorn (Production WSGI)
```bash
source venv/bin/activate
gunicorn -w 3 -b 0.0.0.0:8000 app_refactored:create_app()
```

## 6. [Optional] Nginx Reverse Proxy
Configure Nginx to proxy requests to Gunicorn on port 8000.

## 7. GitHub Actions CI/CD
- Your `.github/workflows/deploy.yml` will run `pytest` before deploying.
- Ensure all tests pass locally before pushing.

## 8. Troubleshooting
- Check logs for errors: `journalctl -u your-app.service` or `gunicorn.log`
- Ensure all environment variables are set in production.

---

**For more help, see the README or open an issue on GitHub.** 