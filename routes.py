from flask import Blueprint, render_template, request, send_file, session, redirect, url_for, flash, abort, current_app
from flask_mail import Message
from werkzeug.exceptions import BadRequest, Unauthorized
import json
from datetime import datetime

from models import User, Invoice
from utils import InvoiceProcessor, SessionManager, EmailValidator
from extensions import mail, db
from stripe_integration import create_checkout_session, handle_webhook_event, get_payment_status

# Create blueprints for better organization
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
invoice = Blueprint('invoice', __name__)
stripe_bp = Blueprint('stripe', __name__)

# Main routes
@main.route('/')
def form():
    """Display the invoice form"""
    return render_template('form.html')

@main.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main.route('/premium')
def premium():
    """Premium features page"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    return render_template('premium.html')

# Invoice routes
@invoice.route('/preview', methods=['POST'])
def preview():
    """Preview invoice before generating"""
    try:
        data = InvoiceProcessor.process_form_data(request.form.to_dict(flat=True))
        SessionManager.store_invoice_data(data)
        
        # Pre-render invoice
        invoice_html = render_template("invoice.html", data=data)
        return render_template('preview.html', data=data, invoice_html=invoice_html)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('main.form'))

@invoice.route('/invoice_preview')
def invoice_preview():
    """Display invoice preview from session"""
    data = SessionManager.get_invoice_data()
    if not data:
        return "No invoice to preview", 400
    return render_template("invoice.html", data=data)

@invoice.route('/edit')
def edit():
    """Edit the last invoice"""
    data = SessionManager.get_invoice_data()
    if not data:
        return redirect(url_for('main.form'))
    return render_template('form.html', data=data)

@invoice.route('/download', methods=['POST'])
def download():
    """Generate and download PDF invoice"""
    try:
        data = InvoiceProcessor.process_form_data(request.form.to_dict(flat=True))
        
        # Validate required fields
        if not all(key in data for key in ['your_name', 'client_name', 'description']):
            raise BadRequest("Missing required fields")
        
        html = render_template('invoice.html', data=data)
        filename = InvoiceProcessor.generate_filename(data['your_name'])
        pdf_path = InvoiceProcessor.create_pdf(html, filename)
        
        # Debug logging for database save
        current_app.logger.info(f"PDF generated successfully: {filename}")
        current_app.logger.info(f"User authenticated: {SessionManager.is_authenticated()}")
        current_app.logger.info(f"Review field value: {data.get('review')}")
        current_app.logger.info(f"Should save to DB: {SessionManager.is_authenticated() and not data.get('review')}")
        
        # Save to database if user is logged in
        if SessionManager.is_authenticated() and not data.get('review'):
            current_app.logger.info(f"Saving invoice to database for user {session['user']['id']}")
            invoice_record = Invoice(
                user_id=session["user"]["id"],
                data=data,
            )
            db.session.add(invoice_record)
            db.session.commit()
            current_app.logger.info(f"Invoice saved successfully with ID: {invoice_record.id}")
        else:
            current_app.logger.info("Invoice not saved to database (user not authenticated or review mode)")
        
        return send_file(pdf_path, as_attachment=True, download_name=filename)
    except Exception as e:
        current_app.logger.error(f"Error in download: {str(e)}")
        flash(f"Error generating PDF: {str(e)}", 'error')
        return redirect(url_for('main.form'))

@invoice.route('/email_invoice', methods=['POST'])
def email_invoice():
    """Email invoice to client"""
    try:
        data = InvoiceProcessor.process_form_data(request.form.to_dict(flat=True))
        
        # Validate email
        client_email = data.get('client_email', '').strip()
        if not EmailValidator.is_valid_email(client_email):
            raise ValueError("Invalid client email address")
        
        html = render_template('invoice.html', data=data)
        pdf_path = InvoiceProcessor.create_pdf(html, 'invoice.pdf')
        
        msg = Message(
            subject="Your Invoice",
            recipients=[client_email]
        )
        msg.body = "Please find your invoice attached."
        
        with open(pdf_path, 'rb') as f:
            msg.attach("invoice.pdf", "application/pdf", f.read())
        
        mail.send(msg)
        
        # Debug logging for database save
        current_app.logger.info(f"Email sent successfully to {client_email}")
        current_app.logger.info(f"User authenticated: {SessionManager.is_authenticated()}")
        current_app.logger.info(f"Review field value: {data.get('review')}")
        current_app.logger.info(f"Should save to DB: {SessionManager.is_authenticated() and not data.get('review')}")
        
        # Save to database if user is logged in
        if SessionManager.is_authenticated() and not data.get('review'):
            current_app.logger.info(f"Saving invoice to database for user {session['user']['id']}")
            invoice_record = Invoice(
                user_id=session["user"]["id"],
                data=data,
            )
            db.session.add(invoice_record)
            db.session.commit()
            current_app.logger.info(f"Invoice saved successfully with ID: {invoice_record.id}")
        else:
            current_app.logger.info("Invoice not saved to database (user not authenticated or review mode)")
        
        # Store data in session for success page
        SessionManager.store_invoice_data(data)
        return redirect(url_for('invoice.email_success'))
    except Exception as e:
        current_app.logger.error(f"Error in email_invoice: {str(e)}")
        flash(f"Error sending email: {str(e)}", 'error')
        return redirect(url_for('main.form'))

@invoice.route('/email_success')
def email_success():
    """Display email success page"""
    data = SessionManager.get_invoice_data()
    if not data:
        flash("No invoice data found", 'error')
        return redirect(url_for('main.form'))
    return render_template('email_success.html', data=data)

@invoice.route("/history")
def history():
    """Display user's invoice history"""
    current_app.logger.info(f"History route accessed. Session: {session}")
    
    if not SessionManager.is_authenticated():
        current_app.logger.info("User not authenticated, redirecting to login")
        return redirect(url_for('auth.login'))
    
    # Get user from database and check premium status directly
    user = User.query.get(session["user"]["id"])
    current_app.logger.info(f"User from DB: {user}")
    
    if not user:
        current_app.logger.info("User not found in DB, redirecting to logout")
        return redirect(url_for('auth.logout'))
    
    # Check premium status from database, not session
    current_app.logger.info(f"User premium status: {user.is_premium}")
    if not user.is_premium:
        current_app.logger.info("User not premium, redirecting to premium page")
        return redirect(url_for('main.premium'))
    
    invoices = user.invoices
    current_app.logger.info(f"Found {len(invoices)} invoices for user")
    
    return render_template("history.html", invoices=invoices)

@invoice.route("/<int:invoice_id>")
def view_invoice(invoice_id):
    """View a specific invoice"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check authorization
    if session["user"]["id"] != invoice.user_id:
        abort(403, description="Unauthorized access to invoice")
    
    return render_template("view_invoice.html", invoice=invoice, invoice_data=invoice.invoice_data)

@invoice.route("/buy-premium")
def buy_premium():
    """Upgrade user to premium"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=session["user"]["email"]).first()
    if user:
        user.is_premium = True
        db.session.commit()
        session["user"]["is_premium"] = True
        flash("Successfully upgraded to premium!", 'success')
    
    return redirect(url_for('invoice.history'))

# Stripe routes
@stripe_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout():
    """Create Stripe checkout session for premium purchase"""
    if not SessionManager.is_authenticated():
        return {'error': 'Not authenticated'}, 401
    
    try:
        user_email = session["user"]["email"]
        user_id = session["user"]["id"]
        
        checkout_session = create_checkout_session(user_email, user_id)
        
        return {'sessionId': checkout_session.id}
        
    except Exception as e:
        current_app.logger.error(f"Error creating checkout session: {str(e)}")
        return {'error': 'Failed to create checkout session'}, 500

@stripe_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        return {'error': 'No signature'}, 400
    
    success = handle_webhook_event(payload, sig_header)
    
    if success:
        return {'status': 'success'}, 200
    else:
        return {'error': 'Webhook processing failed'}, 400

@stripe_bp.route('/success')
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Payment session not found', 'error')
        return redirect(url_for('main.premium'))
    
    # Get payment status
    payment_info = get_payment_status(session_id)
    
    if payment_info and payment_info['status'] == 'paid':
        # Update session if user is logged in
        if SessionManager.is_authenticated():
            user = User.query.get(session["user"]["id"])
            if user:
                user.is_premium = True
                db.session.commit()
                session["user"]["is_premium"] = True
        
        flash('Payment successful! You are now a premium user.', 'success')
        return redirect(url_for('invoice.history'))
    else:
        flash('Payment verification failed', 'error')
        return redirect(url_for('main.premium'))

@stripe_bp.route('/cancel')
def payment_cancel():
    """Handle cancelled payment"""
    flash('Payment was cancelled', 'info')
    return redirect(url_for('main.premium')) 