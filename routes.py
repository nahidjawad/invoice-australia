from flask import Blueprint, render_template, request, send_file, session, redirect, url_for, flash, abort, current_app, jsonify
from flask_mail import Message
from werkzeug.exceptions import BadRequest, Unauthorized
import json
from datetime import datetime
import hashlib

from models import User, Invoice, AdvancedInvoice, AdvancedInvoiceItem, Company
from utils import InvoiceProcessor, SessionManager, EmailValidator
from extensions import mail, db
from stripe_integration import create_checkout_session, handle_webhook_event, get_payment_status

# Create blueprints for better organization
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
invoice = Blueprint('invoice', __name__)
advanced_invoice = Blueprint('advanced_invoice', __name__)
stripe_bp = Blueprint('stripe', __name__)
user = Blueprint('user', __name__)

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

@main.route('/contact/feedback', methods=['POST'])
def contact_feedback():
    data = request.get_json()
    website = data.get('website', '')
    if website:
        # Honeypot triggered, treat as spam
        return {'success': True, 'message': 'Thank you for your feedback!'}
    feedback_type = data.get('type')
    message = data.get('message')
    name = data.get('name')
    email = data.get('email')
    if not feedback_type or not message or not email:
        return {'success': False, 'message': 'All fields are required.'}, 400
    try:
        mail_msg = Message(
            subject=f"[Feedback] {feedback_type.title()} from {name or 'Anonymous'}",
            recipients=[current_app.config['FEEDBACK_RECIPIENT']],
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            reply_to=email
        )
        mail_msg.body = f"Type: {feedback_type}\nFrom: {name} <{email}>\n\nMessage:\n{message}"
        mail.send(mail_msg)
        return {'success': True, 'message': 'Thank you for your feedback!'}
    except Exception as e:
        current_app.logger.error(f"Feedback email failed: {str(e)}")
        return {'success': False, 'message': 'Failed to send feedback. Please try again later.'}, 500

# Advanced Invoice routes
@advanced_invoice.route('/')
def advanced_form():
    """Display the advanced invoice form"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user']['id'])
    user_companies = user.companies if user else []
    
    return render_template('advanced_form.html', user_companies=user_companies)

@advanced_invoice.route('/preview', methods=['POST'])
def advanced_preview():
    """Preview advanced invoice before generating"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    try:
        data = process_advanced_form_data(request.form.to_dict(flat=True))
        SessionManager.store_advanced_invoice_data(data)
        
        # Pre-render invoice
        invoice_html = render_template("advanced_invoice.html", data=data)
        return render_template('advanced_preview.html', data=data, invoice_html=invoice_html)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('advanced_invoice.advanced_form'))

@advanced_invoice.route('/download', methods=['POST'])
def advanced_download():
    """Download advanced invoice PDF using session data"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    try:
        data = SessionManager.get_advanced_invoice_data()
        current_app.logger.info(f"Session data retrieved: {data is not None}")
        if data:
            current_app.logger.info(f"Data keys: {list(data.keys()) if data else 'None'}")
        
        if not data:
            flash("No invoice data found", 'error')
            return redirect(url_for('advanced_invoice.advanced_form'))
        
        html = render_template('advanced_invoice.html', data=data)
        filename = InvoiceProcessor.generate_filename(data.get('sender_name', 'Advanced_Invoice'))
        pdf_path = InvoiceProcessor.create_pdf(html, filename)
        
        # Save to database
        save_advanced_invoice_once(session["user"]["id"], data)
        
        return send_file(pdf_path, as_attachment=True, download_name=filename)
    except Exception as e:
        current_app.logger.error(f"Error in advanced download: {str(e)}")
        flash(f"Error generating PDF: {str(e)}", 'error')
        return redirect(url_for('advanced_invoice.advanced_form'))

@advanced_invoice.route('/email', methods=['POST'])
def advanced_email():
    """Email advanced invoice using session data"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    try:
        data = SessionManager.get_advanced_invoice_data()
        if not data:
            flash("No invoice data found", 'error')
            return redirect(url_for('advanced_invoice.advanced_form'))
        
        # Validate email
        client_email = data.get('client_email', '').strip()
        if not EmailValidator.is_valid_email(client_email):
            raise ValueError("Invalid client email address")
        
        html = render_template('advanced_invoice.html', data=data)
        pdf_path = InvoiceProcessor.create_pdf(html, 'advanced_invoice.pdf')
        
        msg = Message(
            subject="Your Invoice",
            recipients=[client_email]
        )
        msg.body = "Please find your invoice attached."
        
        with open(pdf_path, 'rb') as f:
            msg.attach("invoice.pdf", "application/pdf", f.read())
        
        mail.send(msg)
        
        # Save to database
        save_advanced_invoice_once(session["user"]["id"], data)
        
        # Store data in session for success page
        SessionManager.store_advanced_invoice_data(data)
        return redirect(url_for('advanced_invoice.advanced_email_success'))
    except Exception as e:
        current_app.logger.error(f"Error in advanced email: {str(e)}")
        flash(f"Error sending email: {str(e)}", 'error')
        return redirect(url_for('advanced_invoice.advanced_form'))

@advanced_invoice.route('/edit')
def advanced_edit():
    """Edit the last advanced invoice from session data"""
    data = SessionManager.get_advanced_invoice_data()
    if not data:
        flash("No invoice data found", 'error')
        return redirect(url_for('advanced_invoice.advanced_form'))
    
    # Get user companies for the dropdown
    user = User.query.get(session['user']['id'])
    user_companies = user.companies if user else []
    
    # Debug logging
    current_app.logger.info(f"Edit route - Data keys: {list(data.keys()) if data else 'None'}")
    if data and 'invoice_items' in data:
        current_app.logger.info(f"Edit route - Number of items: {len(data['invoice_items'])}")
        for i, item in enumerate(data['invoice_items']):
            current_app.logger.info(f"Edit route - Item {i}: {item}")
    
    return render_template('advanced_form.html', data=data, user_companies=user_companies)

@advanced_invoice.route('/email-success')
def advanced_email_success():
    """Display advanced email success page"""
    data = SessionManager.get_advanced_invoice_data()
    if not data:
        flash("No invoice data found", 'error')
        return redirect(url_for('advanced_invoice.advanced_form'))
    return render_template('advanced_email_success.html', data=data)

@advanced_invoice.route('/<int:invoice_id>')
def view_advanced_invoice(invoice_id):
    """View a specific advanced invoice"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    advanced_invoice = AdvancedInvoice.query.get_or_404(invoice_id)
    
    # Check if user owns this invoice
    if advanced_invoice.user_id != session['user']['id']:
        abort(403)
    
    data = prepare_advanced_invoice_data(advanced_invoice)
    return render_template('view_advanced_invoice.html', invoice=advanced_invoice, invoice_data=data)

def process_advanced_form_data(form_data):
    """Process advanced invoice form data"""
    data = {}
    
    # Basic invoice details
    data['invoice_number'] = form_data.get('invoice_number', '').strip()
    data['date'] = form_data.get('date', '').strip()
    data['client_name'] = form_data.get('client_name', '').strip()
    data['client_email'] = form_data.get('client_email', '').strip()
    data['include_gst'] = form_data.get('include_gst') == 'on'
    
    # Sender details
    sender_type = form_data.get('sender_type', 'personal')
    data['use_company'] = sender_type == 'company'
    
    if data['use_company']:
        company_id = form_data.get('company_id')
        if not company_id:
            raise ValueError("Please select a company")
        
        company = Company.query.get(company_id)
        if not company:
            raise ValueError("Selected company not found")
        
        data['company_id'] = company_id
        data['sender_name'] = company.company_name
        data['sender_abn'] = company.abn
        data['sender_address'] = company.address
        data['sender_phone'] = company.phone
        data['sender_email'] = company.email
        data['sender_logo'] = company.logo_path
    else:
        data['your_name'] = form_data.get('your_name', '').strip()
        data['abn'] = form_data.get('abn', '').strip()
        data['sender_name'] = data['your_name']
        data['sender_abn'] = data['abn']
    
    # Process items
    items = []
    item_index = 0
    
    while f'items[{item_index}][description]' in form_data:
        description = form_data.get(f'items[{item_index}][description]', '').strip()
        quantity = float(form_data.get(f'items[{item_index}][quantity]', 1))
        rate = float(form_data.get(f'items[{item_index}][rate]', 0))
        
        if description and rate > 0:
            total = quantity * rate
            items.append({
                'description': description,
                'quantity': quantity,
                'rate': rate,
                'total': total
            })
        
        item_index += 1
    
    if not items:
        raise ValueError("At least one item is required")
    
    data['invoice_items'] = items
    
    # Calculate totals
    subtotal = sum(item['total'] for item in items)
    gst_amount = subtotal * 0.1 if data['include_gst'] else 0
    total = subtotal + gst_amount
    
    data['subtotal'] = subtotal
    data['gst_amount'] = gst_amount
    data['total'] = total
    
    # Format date
    try:
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
        data['formatted_date'] = date_obj.strftime('%d/%m/%Y')
    except ValueError:
        data['formatted_date'] = data['date']
    
    return data

def save_advanced_invoice_once(user_id, data):
    """Save advanced invoice to DB only if not already saved in session."""
    invoice_str = json.dumps(data, sort_keys=True)
    invoice_hash = hashlib.sha256(invoice_str.encode()).hexdigest()
    
    if session.get('last_advanced_invoice_hash') != invoice_hash:
        # Create advanced invoice
        advanced_invoice = AdvancedInvoice(
            user_id=user_id,
            invoice_number=data['invoice_number'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            client_name=data['client_name'],
            client_email=data['client_email'],
            include_gst=data['include_gst'],
            subtotal=data['subtotal'],
            gst_amount=data['gst_amount'],
            total=data['total'],
            use_company=data['use_company'],
            company_id=data.get('company_id'),
            your_name=data.get('your_name'),
            abn=data.get('abn')
        )
        
        db.session.add(advanced_invoice)
        db.session.flush()  # Get the ID
        
        # Create invoice items
        for item_data in data['invoice_items']:
            item = AdvancedInvoiceItem(
                advanced_invoice_id=advanced_invoice.id,
                description=item_data['description'],
                quantity=item_data['quantity'],
                rate=item_data['rate'],
                total=item_data['total']
            )
            db.session.add(item)
        
        db.session.commit()
        session['last_advanced_invoice_hash'] = invoice_hash
        session['last_advanced_invoice_id'] = advanced_invoice.id
        current_app.logger.info(f"Advanced invoice saved successfully with ID: {advanced_invoice.id}")
    else:
        current_app.logger.info("Advanced invoice already saved for this data, skipping DB save.")

def prepare_advanced_invoice_data(advanced_invoice):
    """Prepare advanced invoice data for template rendering"""
    data = {
        'invoice_number': advanced_invoice.invoice_number,
        'date': advanced_invoice.date.strftime('%Y-%m-%d'),
        'formatted_date': advanced_invoice.date.strftime('%d/%m/%Y'),
        'client_name': advanced_invoice.client_name,
        'client_email': advanced_invoice.client_email,
        'include_gst': advanced_invoice.include_gst,
        'subtotal': advanced_invoice.subtotal,
        'gst_amount': advanced_invoice.gst_amount,
        'total': advanced_invoice.total,
        'use_company': advanced_invoice.use_company,
        'company_id': advanced_invoice.company_id,
        'your_name': advanced_invoice.your_name,
        'abn': advanced_invoice.abn,
        'invoice_items': []
    }
    
    # Get sender details
    sender_details = advanced_invoice.get_sender_details()
    data.update(sender_details)
    
    # Add sender_name for template compatibility
    if advanced_invoice.use_company and advanced_invoice.company:
        data['sender_name'] = advanced_invoice.company.company_name
        data['sender_abn'] = advanced_invoice.company.abn
    else:
        data['sender_name'] = advanced_invoice.your_name
        data['sender_abn'] = advanced_invoice.abn
    
    # Get items
    for item in advanced_invoice.items:
        data['invoice_items'].append({
            'description': item.description,
            'quantity': item.quantity,
            'rate': item.rate,
            'total': item.total
        })
    
    return data

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

def save_invoice_once(user_id, data):
    """Save invoice to DB only if not already saved in session."""
    invoice_str = json.dumps(data, sort_keys=True)
    invoice_hash = hashlib.sha256(invoice_str.encode()).hexdigest()
    if session.get('last_invoice_hash') != invoice_hash:
        invoice_record = Invoice(
            user_id=user_id,
            data=data,
        )
        db.session.add(invoice_record)
        db.session.commit()
        session['last_invoice_hash'] = invoice_hash
        session['last_invoice_id'] = invoice_record.id
        current_app.logger.info(f"Invoice saved successfully with ID: {invoice_record.id}")
    else:
        current_app.logger.info("Invoice already saved for this data, skipping DB save.")

@invoice.route('/download', methods=['POST'])
def download():
    """Generate and download PDF invoice (simple or advanced)"""
    try:
        # Check if this is an advanced invoice by looking for items array
        form_data = request.form.to_dict(flat=True)
        
        if 'items[0][description]' in form_data:
            # This is an advanced invoice
            data = process_advanced_form_data(form_data)
            
            # Validate required fields
            if not all(key in data for key in ['client_name', 'invoice_number', 'date']):
                raise BadRequest("Missing required fields")
            
            if not data.get('invoice_items'):
                raise BadRequest("At least one item is required")
            
            html = render_template('advanced_invoice.html', data=data)
            filename = InvoiceProcessor.generate_filename(data.get('sender_name', 'Advanced_Invoice'))
            pdf_path = InvoiceProcessor.create_pdf(html, filename)
            
            # Save to database if user is logged in and not reviewing from history
            if SessionManager.is_authenticated() and not data.get('review'):
                save_advanced_invoice_once(session["user"]["id"], data)
            
        else:
            # This is a simple invoice
            data = InvoiceProcessor.process_form_data(form_data)
            
            # Validate required fields
            if not all(key in data for key in ['your_name', 'client_name', 'description']):
                raise BadRequest("Missing required fields")
            
            html = render_template('invoice.html', data=data)
            filename = InvoiceProcessor.generate_filename(data['your_name'])
            pdf_path = InvoiceProcessor.create_pdf(html, filename)
            
            # Save to database if user is logged in and invoice not already saved
            if SessionManager.is_authenticated() and not data.get('review'):
                save_invoice_once(session["user"]["id"], data)
        
        return send_file(pdf_path, as_attachment=True, download_name=filename)
    except Exception as e:
        current_app.logger.error(f"Error in download: {str(e)}")
        flash(f"Error generating PDF: {str(e)}", 'error')
        return redirect(url_for('main.form'))

@invoice.route('/email_invoice', methods=['POST'])
def email_invoice():
    """Email invoice to client (simple or advanced)"""
    try:
        # Check if this is an advanced invoice by looking for items array
        form_data = request.form.to_dict(flat=True)
        
        if 'items[0][description]' in form_data:
            # This is an advanced invoice
            data = process_advanced_form_data(form_data)
            
            # Validate email
            client_email = data.get('client_email', '').strip()
            if not EmailValidator.is_valid_email(client_email):
                raise ValueError("Invalid client email address")
            
            html = render_template('advanced_invoice.html', data=data)
            pdf_path = InvoiceProcessor.create_pdf(html, 'advanced_invoice.pdf')
            
            msg = Message(
                subject="Your Invoice",
                recipients=[client_email]
            )
            msg.body = "Please find your invoice attached."
            
            with open(pdf_path, 'rb') as f:
                msg.attach("invoice.pdf", "application/pdf", f.read())
            
            mail.send(msg)
            
            # Save to database if user is logged in and not reviewing from history
            if SessionManager.is_authenticated() and not data.get('review'):
                save_advanced_invoice_once(session["user"]["id"], data)
            
            # Store data in session for success page
            SessionManager.store_advanced_invoice_data(data)
            return redirect(url_for('advanced_invoice.advanced_email_success'))
            
        else:
            # This is a simple invoice
            data = InvoiceProcessor.process_form_data(form_data)
            
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
            
            # Save to database if user is logged in and invoice not already saved
            if SessionManager.is_authenticated() and not data.get('review'):
                save_invoice_once(session["user"]["id"], data)
            
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
    """Display combined invoice history (simple and advanced)"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    user_id = session['user']['id']
    
    # Get simple invoices
    simple_invoices = Invoice.query.filter_by(user_id=user_id).order_by(Invoice.created_at.desc()).all()
    
    # Get advanced invoices
    advanced_invoices = AdvancedInvoice.query.filter_by(user_id=user_id).order_by(AdvancedInvoice.created_at.desc()).all()
    
    # Combine and sort by creation date
    all_invoices = []
    
    # Add simple invoices with type indicator
    for invoice in simple_invoices:
        all_invoices.append({
            'id': invoice.id,
            'invoice_number': invoice.invoice_data.get('invoice_number', 'N/A'),
            'date': invoice.created_at,
            'client_name': invoice.invoice_data.get('client_name', 'N/A'),
            'total': invoice.invoice_data.get('total', 0),
            'status': invoice.status,
            'type': 'simple',
            'include_gst': invoice.invoice_data.get('include_gst', False),
            'items_count': 1  # Simple invoices always have 1 item
        })
    
    # Add advanced invoices with type indicator
    for invoice in advanced_invoices:
        all_invoices.append({
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'date': invoice.created_at,
            'client_name': invoice.client_name,
            'total': invoice.total,
            'status': invoice.status,
            'type': 'advanced',
            'include_gst': invoice.include_gst,
            'items_count': len(invoice.items)
        })
    
    # Sort by date (newest first)
    all_invoices.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('history.html', invoices=all_invoices)

@invoice.route("/<int:invoice_id>")
def view_invoice(invoice_id):
    """View a specific invoice (simple or advanced)"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    current_app.logger.info(f"Viewing invoice ID: {invoice_id}")
    
    # Try to find as simple invoice first
    invoice = Invoice.query.get(invoice_id)
    if invoice and invoice.user_id == session['user']['id']:
        current_app.logger.info(f"Found simple invoice: {invoice.id}")
        return render_template('view_invoice.html', invoice=invoice, invoice_data=invoice.invoice_data)
    
    # Try to find as advanced invoice
    advanced_invoice = AdvancedInvoice.query.get(invoice_id)
    if advanced_invoice and advanced_invoice.user_id == session['user']['id']:
        current_app.logger.info(f"Found advanced invoice: {advanced_invoice.id}")
        data = prepare_advanced_invoice_data(advanced_invoice)
        return render_template('view_advanced_invoice.html', invoice=advanced_invoice, invoice_data=data)
    
    # If neither found or user doesn't own it
    current_app.logger.warning(f"No invoice found with ID: {invoice_id}")
    abort(404)

@invoice.route("/buy-premium")
def buy_premium():
    """Buy premium subscription"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user']['id'])
    if user.is_premium:
        flash('You are already a premium user!', 'info')
        return redirect(url_for('main.premium'))
    
    return render_template('buy_premium.html')

@invoice.route('/mark_paid/<int:invoice_id>', methods=['POST'])
def mark_paid(invoice_id):
    """Mark invoice as paid (simple or advanced)"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    # Try to find as simple invoice first
    invoice = Invoice.query.get(invoice_id)
    if invoice and invoice.user_id == session['user']['id']:
        invoice.status = 'Paid'
        db.session.commit()
        flash('Invoice marked as paid!', 'success')
        return redirect(url_for('invoice.view_invoice', invoice_id=invoice_id))
    
    # Try to find as advanced invoice
    advanced_invoice = AdvancedInvoice.query.get(invoice_id)
    if advanced_invoice and advanced_invoice.user_id == session['user']['id']:
        advanced_invoice.status = 'Paid'
        db.session.commit()
        flash('Invoice marked as paid!', 'success')
        return redirect(url_for('invoice.view_invoice', invoice_id=invoice_id))
    
    # If neither found or user doesn't own it
    abort(404)

@invoice.route('/mark_paid_ajax/<int:invoice_id>', methods=['POST'])
def mark_paid_ajax(invoice_id):
    """Mark invoice as paid via AJAX (returns JSON)"""
    if not SessionManager.is_authenticated():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Try to find as simple invoice first
        invoice = Invoice.query.get(invoice_id)
        if invoice and invoice.user_id == session['user']['id']:
            invoice.status = 'Paid'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Invoice marked as paid!'})
        
        # Try to find as advanced invoice
        advanced_invoice = AdvancedInvoice.query.get(invoice_id)
        if advanced_invoice and advanced_invoice.user_id == session['user']['id']:
            advanced_invoice.status = 'Paid'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Invoice marked as paid!'})
        
        # If neither found or user doesn't own it
        return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
    except Exception as e:
        current_app.logger.error(f"Error marking invoice as paid: {str(e)}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@stripe_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout():
    """Create Stripe checkout session"""
    if not SessionManager.is_authenticated():
        return {'error': 'Not authenticated'}, 401
    
    try:
        session_url = create_checkout_session(session['user']['id'])
        return {'session_url': session_url}
    except Exception as e:
        current_app.logger.error(f"Error creating checkout session: {str(e)}")
        return {'error': 'Failed to create checkout session'}, 500

@stripe_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events"""
    try:
        handle_webhook_event(request)
        return {'success': True}
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        return {'error': 'Webhook processing failed'}, 400

@stripe_bp.route('/success')
def payment_success():
    """Handle successful payment"""
    if not SessionManager.is_authenticated():
        return redirect(url_for('auth.login'))
    
    session_id = request.args.get('session_id')
    if not session_id:
        flash('No session ID provided', 'error')
        return redirect(url_for('main.premium'))
    
    try:
        status = get_payment_status(session_id)
        if status == 'complete':
            # Update user to premium
            user = User.query.get(session['user']['id'])
            user.is_premium = True
            db.session.commit()
            
            flash('Payment successful! You are now a premium user.', 'success')
            return redirect(url_for('main.premium'))
        else:
            flash('Payment not completed', 'error')
            return redirect(url_for('main.premium'))
    except Exception as e:
        current_app.logger.error(f"Payment success error: {str(e)}")
        flash('Error processing payment', 'error')
        return redirect(url_for('main.premium'))

@stripe_bp.route('/cancel')
def payment_cancel():
    """Handle cancelled payment"""
    flash('Payment was cancelled', 'info')
    return redirect(url_for('main.premium')) 
