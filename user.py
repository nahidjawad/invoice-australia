from flask import Blueprint, session, redirect, url_for, flash, current_app, render_template, request, jsonify
from models import User
from extensions import db

user = Blueprint('user', __name__)

@user.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        if request.is_json:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        return redirect(url_for("auth.login"))

    user_obj = User.query.get(session["user"]["id"])
    if not user_obj:
        if request.is_json:
            return jsonify({"success": False, "message": "User not found"}), 404
        flash("User not found.", "error")
        return redirect(url_for("main.form"))

    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            updated = False

            # Update fields if present in the request
            if "name" in data and data["name"]:
                user_obj.name = data["name"]
                updated = True
            if "phone" in data:
                user_obj.phone = data["phone"]
                updated = True
            if "address" in data:
                user_obj.address = data["address"]
                updated = True
            if "gender" in data:
                user_obj.gender = data["gender"]
                updated = True
            if "dob" in data and data["dob"]:
                from datetime import datetime
                try:
                    user_obj.dob = datetime.strptime(data["dob"], "%Y-%m-%d").date()
                    updated = True
                except Exception:
                    return jsonify({"success": False, "message": "Invalid date format."}), 400

            if updated:
                db.session.commit()
                return jsonify({"success": True, "message": "Profile updated!"})
            else:
                return jsonify({"success": False, "message": "No valid fields to update."}), 400

    return render_template("profile.html", user=user_obj)