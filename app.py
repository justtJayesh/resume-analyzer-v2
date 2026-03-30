import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

import database
import analyzer

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Initialize database on startup
with app.app_context():
    database.init_db()


def login_required(f):
    """Decorator to require login for a route. Returns JSON 401 for AJAX requests."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.headers.get("Content-Type") == "application/json" or request.is_json:
                return jsonify({"success": False, "error": "Please log in to access this page."}), 401
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


@app.route("/delete-analysis/<int:analysis_id>", methods=["POST"])
@login_required
def delete_analysis(analysis_id):
    """Delete a specific analysis."""
    success = database.delete_analysis(analysis_id, session["user_id"])
    if success:
        flash("Analysis deleted.", "success")
    else:
        flash("Could not delete analysis.", "error")
    return redirect(url_for("analysis"))


@app.route("/feedback/<int:analysis_id>", methods=["POST"])
@login_required
def submit_feedback(analysis_id):
    """Submit feedback (star rating + optional comment) for an analysis."""
    rating_str = request.form.get("rating", "")
    try:
        rating = int(rating_str)
        if rating < 1 or rating > 5:
            return jsonify({"success": False, "error": "Rating must be between 1 and 5."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid rating."}), 400

    comment = request.form.get("comment", "").strip() or None

    analysis = database.get_analysis_by_id(analysis_id, session["user_id"])
    if not analysis:
        return jsonify({"success": False, "error": "Analysis not found."}), 403

    try:
        database.update_feedback(analysis_id, session["user_id"], rating, comment)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 409

    return jsonify({"success": True})


@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    """Home page - upload resume and view score/tips."""
    # Handle POST: file upload
    if request.method == "POST":
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

        # Get job title and job description if provided
        job_title = request.form.get("job_title", "").strip()
        job_description = request.form.get("job_description", "").strip()

        text = analyzer.extract_text_from_file(file_content, file.filename)
        score, tips, detailed_results = analyzer.analyze_resume(text, job_description if job_description else None)

        # Save analysis to database
        analysis_id = database.add_analysis(
            session["user_id"],
            file.filename,
            score,
            tips,
            detailed_results,
            job_title if job_title else None,
            job_description if job_description else None
        )

        # Store results in session for PRG pattern
        session["last_analysis"] = {
            "id": analysis_id,
            "filename": file.filename,
            "score": score,
            "tips": tips,
            "detailed_results": detailed_results,
            "job_title": job_title if job_title else None,
            "job_description": job_description if job_description else None
        }

        flash("Resume analyzed successfully!", "success")
        return redirect(url_for("home", _anchor="analysis-results"))

    # GET request: show page with any stored results
    # Pop results from session if they exist (one-time display)
    last_analysis = session.pop("last_analysis", None)

    # Check if feedback was already submitted for this analysis
    last_analysis_id = last_analysis["id"] if last_analysis else None
    last_analysis_feedback = None
    if last_analysis_id:
        # Fetch fresh from DB to get feedback status
        db_analysis = database.get_analysis_by_id(last_analysis_id, session["user_id"])
        if db_analysis:
            last_analysis_feedback = {
                "rating": db_analysis.get("feedback_rating"),
                "comment": db_analysis.get("feedback_comment"),
            }

    return render_template(
        "home.html",
        last_analysis_id=last_analysis_id,
        last_analysis_feedback=last_analysis_feedback,
        last_filename=last_analysis["filename"] if last_analysis else None,
        last_score=last_analysis["score"] if last_analysis else None,
        last_tips=last_analysis["tips"] if last_analysis else None,
        last_detailed=last_analysis.get("detailed_results") if last_analysis else None,
        last_job_title=last_analysis.get("job_title") if last_analysis else None,
        last_job_description=last_analysis.get("job_description") if last_analysis else None,
    )


@app.route("/analysis")
@login_required
def analysis():
    """Analysis history page - shows all past analyses in a table."""
    analyses = database.get_analyses_by_user(session["user_id"], limit=None)
    return render_template("analysis.html", analyses=analyses)


@app.route("/analysis/<int:analysis_id>")
@login_required
def analysis_detail(analysis_id):
    """Analysis detail page - shows full details of a specific analysis."""
    analysis = database.get_analysis_by_id(analysis_id, session["user_id"])
    if not analysis:
        flash("Analysis not found.", "error")
        return redirect(url_for("analysis"))
    return render_template("analysis_detail.html", analysis=analysis)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
