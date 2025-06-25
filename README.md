# Invoice Australia

**Create and send tax invoices in seconds.**

Invoice Australia is a lightweight web application that helps individuals and small businesses generate and send tax invoices easily. It supports PDF generation, email delivery, GST calculation, and mobile responsiveness.

## 🚀 Features

- Create tax invoices with client details, quantity, rate, and GST
- Preview and download PDF invoices
- Email invoices to clients
- Fully mobile-responsive design
- Deployed via Flask and PDFKit

---

## 🛠 Installation (CentOS 7)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/invoice-australia.git
cd invoice-australia
```

### 2. Install System Dependencies

```bash
yum update -y
yum install -y epel-release
yum install -y python3 python3-venv python3-pip nginx wkhtmltopdf
```

> ⚠️ If `wkhtmltopdf` is not available in your repo, download the CentOS RPM from: [https://github.com/wkhtmltopdf/wkhtmltopdf/releases](https://github.com/wkhtmltopdf/wkhtmltopdf/releases)

### 3. Set up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_app_password
SECRET_KEY=your_random_secret_key
```

### 5. Run the App

```bash
gunicorn -w 2 -b 127.0.0.1:5000 app:app
```

## 🌐 NGINX Reverse Proxy (Optional)

To serve the app publicly via a subdomain (e.g., `invoice.example.com`), configure NGINX:

```nginx
server {
    listen 80;
    server_name invoice.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        proxy_pass http://127.0.0.1:5000/static/;
        proxy_buffering off;
        proxy_set_header Host $host;
    }
}
```

Then reload NGINX:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 📧 Email Sending Setup

This app uses Gmail SMTP. Make sure:

- You enable "App Passwords" in your Google Account.
- You add the `MAIL_USERNAME` and `MAIL_PASSWORD` correctly in `.env`.

## ✅ Testing (To be implemented)

To test, run the following

```bash
pytest
```

## 📆 Deployment Plan

This app is built to support:

- Automated testing
- CI/CD with GitHub Actions
- Deployment to an EC2 instance

Stay tuned for updates.

---

## 📄 License

MIT License

## ✨ Author

Developed by Nahid Jawad

