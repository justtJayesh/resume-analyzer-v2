# CVNest Project Memory

## Project Overview
- Flask web application for resume analysis
- Analyzes PDF, DOCX, TXT files
- Provides keyword-based score (0-100) with improvement tips
- Users can register, login, upload resumes, view analysis history

## Key Files
- `app.py` - Flask routes (login, register, logout, home, analysis, analysis_detail, delete_analysis)
- `database.py` - SQLite operations (users, analyses tables)
- `analyzer.py` - Resume parsing, scoring, and detailed analysis
- `templates/` - Jinja2 templates
- `Dockerfile` - Docker configuration with Gunicorn

## Database
- SQLite: `instance/resume_analyzer.db`
- Tables: `users`, `analyses`
- Stores: user accounts, resume filenames, scores, tips, detailed_results, job_title, job_description, timestamps

## Running the App
- Development: `python app.py` (runs on http://127.0.0.1:5001)
- Production (Docker): `docker compose up` (Gunicorn on port 5001)
- Tests: `pytest`

## Tech Stack
- Flask
- SQLite
- python-docx (DOCX parsing)
- PyPDF2 (PDF parsing)
- Gunicorn (production server)
- Chart.js (for analytics charts)

## Recent Updates
1. **Gunicorn Timeout Fix**: Added `--timeout 120 --workers 2` to Dockerfile to prevent worker timeouts during long resume analysis
2. **Line Chart on /analysis**: Added Chart.js line chart showing score trend over time, positioned above the analysis table (40vh height)
