from flask import Flask, render_template, request, send_file, session, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
import pdfkit, os
from flask_mail import Mail, Message
import re
from datetime import datetime
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
# db and User are already in scope, defined earlier in app.py
import json


app = Flask(__name__)

load_dotenv()  # Load variables from .env

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD')
)

app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///invoices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# -------------------- MODELS --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    invoices = db.relationship("Invoice", backref="user", lazy=True)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


mail = Mail(app)

@app.context_processor
def inject_user():
    user_data = session.get("user")
    return dict(current_user=user_data)
@app.context_processor
def inject_year():
    return {'year': datetime.now().year}
@app.context_processor
def inject_globals():
    user = session.get("user")
    return {
        "current_user": user,
        "year": datetime.now().year,
        "is_premium": user.get("is_premium") if user else False,
    }



@app.route('/')
def form():
    print("Session contents:", session)
    return render_template('form.html')

@app.route('/invoice_preview')
def invoice_preview():
    from flask import session
    data = session.get("last_invoice_data")
    if not data:
        return "No invoice to preview", 400
    return render_template("invoice.html", data=data)


@app.route('/preview', methods=['POST'])
def preview():
    data = request.form.to_dict(flat=True)
    data['include_gst'] = 'include_gst' in request.form

    # Format date from YYYY-MM-DD to DD/MM/YYYY
    date_str = data.get('date', '')
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            data['formatted_date'] = date_obj.strftime('%d/%m/%Y')  # for invoice display
            data['date'] = date_str  # keep the original ISO format for the form
        except ValueError:
            data['formatted_date'] = date_str  # fallback
    qty = int(data['quantity'])
    rate = float(data['rate'])
    total = qty * rate
    if data['include_gst']:
        total *= 1.10
    data['total'] = round(total, 2)
    data['rate'] = rate
    data['quantity'] = qty
    session["last_invoice_data"] = data
    # Pre-render invoice
    invoice_html = render_template("invoice.html", data=data)
    return render_template('preview.html', data=data, invoice_html=invoice_html)

@app.route('/edit')
def edit():
    data = session.get("last_invoice_data")
    if not data:
        return redirect('/')
    return render_template('form.html', data=data)


@app.route('/download', methods=['POST'])
def download():
    data = request.form.to_dict(flat=True)
    data['include_gst'] = 'include_gst' in request.form
    data['rate'] = float(data['rate'])
    data['quantity'] = int(data['quantity'])
    data['total'] = float(data['total'])

    html = render_template('invoice.html', data=data)

    name_slug = re.sub(r'\W+', '', data['your_name']).lower()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"{name_slug}-{timestamp}.pdf"
    pdf_path = os.path.join('output', filename)

    os.makedirs('output', exist_ok=True)
    pdfkit.from_string(html, pdf_path)

    # Save to database if user is logged in
    if "user" in session and not data.get('review'):
        invoice_record = Invoice(
            user_id=session["user"]["id"],
            data=json.dumps(data),  # <-- Serialize dictionary to string
        )
        db.session.add(invoice_record)
        db.session.commit()


    return send_file(pdf_path, as_attachment=True, download_name=filename)


@app.route('/email', methods=['POST'])
def email_invoice():
    data = request.form.to_dict(flat=True)
    data['include_gst'] = 'include_gst' in request.form
    data['rate'] = float(data['rate'])
    data['quantity'] = int(data['quantity'])
    data['total'] = float(data['total'])

    html = render_template('invoice.html', data=data)
    pdf_path = os.path.join('output', 'invoice.pdf')
    pdfkit.from_string(html, pdf_path)

    msg = Message(
        subject="Your Invoice",
        sender=app.config.get('MAIL_USERNAME'),
        recipients=[data['client_email']]
    )
    msg.body = "Please find your invoice attached."
    with open(pdf_path, 'rb') as f:
        msg.attach("invoice.pdf", "application/pdf", f.read())
    mail.send(msg)

    # Save to database if user is logged in
    if "user" in session and not data.get('review'):
        invoice_record = Invoice(
            user_id=session["user"]["id"],
            data=json.dumps(data),
        )
        db.session.add(invoice_record)
        db.session.commit()


    return render_template("email.html", data=data)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Google OAuth blueprint
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_to="google_login_complete",  # optional: define where to go after login
)
app.register_blueprint(google_bp, url_prefix="/login")

@app.route("/google_login_complete")
def google_login_complete():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info", 400

    user_info = resp.json()

    user = User.query.filter_by(email=user_info["email"]).first()
    if not user:
        user = User(email=user_info["email"], name=user_info["name"])
        db.session.add(user)
        db.session.commit()

    session["user"] = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_premium": user.is_premium
    }


    return redirect(url_for("form"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("form"))

@app.route("/history")
def history():
    if not session.get("user") or not session["user"].get("is_premium"):
        return redirect(url_for("premium"))

    user = User.query.get(session["user"]["id"])
    invoices = user.invoices

    # Convert JSON string to dict
    for invoice in invoices:
        invoice.data = json.loads(invoice.data)

    return render_template("history.html", invoices=invoices)

@app.route("/invoice/<int:invoice_id>")
def view_invoice(invoice_id):
    # Check if user is logged in
    if "user" not in session:
        return redirect(url_for("google.login"))

    invoice = Invoice.query.get_or_404(invoice_id)

    # Only allow the logged-in user to view their own invoice
    if session["user"]["id"] != invoice.user_id:
        return "Unauthorized", 403

    # Convert JSON string to dict
    invoice_data = json.loads(invoice.data)
    return render_template("view_invoice.html", invoice=invoice, invoice_data=invoice_data)


# Example endpoint for buying premium
@app.route("/buy-premium")
def buy_premium():
    if not session.get("user"):
        return redirect(url_for("google.login"))

    user = User.query.filter_by(email=session["user"]["email"]).first()
    session["user"]["is_premium"] = True
    if user:
        user.is_premium = True
        db.session.commit()
        session["user"]["is_premium"] = True

    return redirect(url_for("history"))

@app.route("/premium")
def premium():
    if not session.get("user"):
        return redirect(url_for("google.login"))
    return render_template("premium.html")




if __name__ == '__main__':
    app.run(debug=True)
