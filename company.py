from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, Company, User
import os
from werkzeug.utils import secure_filename

company_bp = Blueprint('company', __name__)

UPLOAD_FOLDER = 'static/uploads/logos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@company_bp.route('/company/list')
def list_companies():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    user = User.query.get(session['user']['id'])
    return render_template('list_companies.html', companies=user.companies)

@company_bp.route('/company/create', methods=['GET', 'POST'])
def create_company():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        company_name = request.form['company_name']
        abn = request.form.get('abn')
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')
        payment_details = request.form.get('payment_details')
        logo_path = None
        # Handle logo upload
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and allowed_file(logo.filename):
                filename = secure_filename(logo.filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                logo.save(os.path.join(UPLOAD_FOLDER, filename))
                logo_path = os.path.join('uploads/logos', filename)
        company = Company(
            company_name=company_name,
            abn=abn,
            address=address,
            phone=phone,
            email=email,
            payment_details=payment_details,
            logo_path=logo_path
        )
        db.session.add(company)
        # Add relationship to current user
        user = User.query.get(session['user']['id'])
        company.users.append(user)
        db.session.commit()
        flash('Company created and linked to your account!', 'success')
        return redirect(url_for('company.list_companies'))
    return render_template('create_company.html')