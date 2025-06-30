from flask import Blueprint, session, redirect, url_for, flash, current_app
from flask_dance.contrib.google import google
from models import User
from extensions import db

auth = Blueprint('auth', __name__)

@auth.route("/google_login_complete")
def google_login_complete():
    """Handle Google OAuth callback"""
    if not google.authorized:
        return redirect(url_for("google.login"))

    try:
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            flash("Failed to fetch user info from Google", "error")
            return redirect(url_for("main.form"))

        user_info = resp.json()
        
        # Find or create user
        user = User.query.filter_by(email=user_info["email"]).first()
        if not user:
            user = User(
                email=user_info["email"], 
                name=user_info["name"]
            )
            db.session.add(user)
            db.session.commit()
            flash("Welcome! Your account has been created.", "success")
        else:
            flash(f"Welcome back, {user.name}!", "success")

        # Store user in session with current premium status from database
        session["user"] = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_premium": bool(user.is_premium)  # Ensure boolean value
        }

        return redirect(url_for("main.form"))
        
    except Exception as e:
        current_app.logger.error(f"OAuth error: {e}")
        flash(f"Login failed: {str(e)}", "error")
        return redirect(url_for("main.form"))

@auth.route("/logout")
def logout():
    """Logout user"""
    session.pop("user", None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("main.form"))

@auth.route("/login")
def login():
    """Redirect to Google OAuth login"""
    return redirect(url_for("google.login")) 