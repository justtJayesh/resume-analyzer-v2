# CVNest

A simple web application to upload your resume and get a keyword-based score with improvement tips.

## Features

- **Login & Registration** - Create an account and sign in
- **Resume Upload** - Supports PDF, DOCX, and TXT files
- **Score & Tips** - Get a score out of 100 and personalized improvement suggestions
- **History** - View your recent analyses

## How to Run Locally

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate it:
   - Mac/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the app:
   ```
   python app.py
   ```

5. Open your browser and go to: http://127.0.0.1:5000

## Tech Stack

- Python + Flask
- HTML + CSS
- SQLite
- PyPDF2, python-docx for file parsing
