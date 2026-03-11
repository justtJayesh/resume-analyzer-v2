# CVNest Project Memory

## Project Overview
- Flask web application for resume analysis
- Analyzes PDF, DOCX, TXT files
- Provides keyword-based score (0-100) with improvement tips
- Users can register, login, upload resumes, view analysis history

## Key Files
- `app.py` - Flask routes (login, register, logout, home)
- `database.py` - SQLite operations
- `analyzer.py` - Resume parsing and scoring
- `templates/` - Jinja2 templates (base.html, auth.html, home.html)

## Running the App
- Runs on http://127.0.0.1:5001
- Command: `python app.py`
- Tests: `pytest`

## Tech Stack
- Flask
- SQLite
- python-docx (DOCX parsing)
- PyPDF2 (PDF parsing)
