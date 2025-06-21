from flask import Flask, render_template, request, send_file, session, redirect, url_for
import pdfkit, os
from flask_mail import Mail, Message
import re
from datetime import datetime
from dotenv import load_dotenv
import os

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

mail = Mail(app)

@app.context_processor
def inject_year():
    return {'year': datetime.now().year}

@app.route('/')
def form():
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

    pdfkit.from_string(html, pdf_path)
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
        sender=app.config.get('MAIL_USERNAME'),  # ✅ safer than direct indexing
        recipients=[data['client_email']]
    )
    msg.body = "Please find your invoice attached."

    with open(pdf_path, 'rb') as f:
        msg.attach("invoice.pdf", "application/pdf", f.read())

    mail.send(msg)

    return render_template("email.html", data=data)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=False)
