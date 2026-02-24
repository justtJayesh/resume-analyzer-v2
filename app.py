import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

import database
import analyzer

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Initialize database on startup
with app.app_context():
    database.init_db()


def login_required(f):
    """Decorator to require login for a route."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    """Redirect root to home or login."""
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page - GET shows form, POST validates and logs in."""
    if request.method == "GET":
        if "user_id" in session:
            return redirect(url_for("home"))
        return render_template("auth.html", active_tab="login")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Please enter both username and password.", "error")
        return render_template("auth.html", active_tab="login")

    user = database.get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid username or password.", "error")
        return render_template("auth.html", active_tab="login")

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    flash("You have been logged in successfully.", "success")
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registration page - GET shows form, POST creates user."""
    if request.method == "GET":
        if "user_id" in session:
            return redirect(url_for("home"))
        return render_template("auth.html", active_tab="register")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")

    errors = []
    if not username:
        errors.append("Username is required.")
    if not email:
        errors.append("Email is required.")
    if not password:
        errors.append("Password is required.")
    if password != confirm:
        errors.append("Passwords do not match.")
    if len(password) < 4:
        errors.append("Password must be at least 4 characters.")

    if errors:
        for err in errors:
            flash(err, "error")
        return render_template("auth.html", active_tab="register")

    if database.get_user_by_username(username):
        flash("Username already exists.", "error")
        return render_template("auth.html", active_tab="register")

    if database.get_user_by_email(email):
        flash("Email already registered.", "error")
        return render_template("auth.html", active_tab="register")

    password_hash = generate_password_hash(password)
    user_id = database.add_user(username, email, password_hash)
    if user_id is None:
        flash("Registration failed. Username or email may already exist.", "error")
        return render_template("auth.html", active_tab="register")

    flash("Registration successful. Please log in.", "success")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """Log out the user."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    """Home page - upload resume and view score/tips. Shows past analyses."""
    if request.method == "GET":
        analyses = database.get_analyses_by_user(session["user_id"])
        return render_template("home.html", analyses=analyses)

    # POST: handle file upload
    if "resume" not in request.files:
        flash("No file was selected.", "error")
        return redirect(url_for("home"))

    file = request.files["resume"]
    if file.filename == "":
        flash("No file was selected.", "error")
        return redirect(url_for("home"))

    if not analyzer.allowed_file(file.filename):
        flash("Invalid file type. Please upload PDF, DOCX, or TXT.", "error")
        return redirect(url_for("home"))

    try:
        file_content = file.read()
    except Exception:
        flash("Error reading file. Please try again.", "error")
        return redirect(url_for("home"))

    text = analyzer.extract_text_from_file(file_content, file.filename)
    score, tips = analyzer.analyze_resume(text)

    # Save analysis to database
    database.add_analysis(session["user_id"], file.filename, score, tips)

    analyses = database.get_analyses_by_user(session["user_id"])
    return render_template(
        "home.html",
        analyses=analyses,
        last_score=score,
        last_tips=tips,
        last_filename=file.filename,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
