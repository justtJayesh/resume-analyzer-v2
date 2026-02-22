"""Resume analyzer - extracts text and computes keyword-based score and tips."""

import re
import io

# Action verbs for scoring
ACTION_VERBS = [
    "managed", "led", "developed", "implemented", "designed", "created",
    "improved", "analyzed", "coordinated", "executed", "built", "delivered"
]

# Resume keywords for scoring
RESUME_KEYWORDS = [
    "experience", "education", "skills", "project", "team", "results",
    "achieved", "responsible", "work", "professional"
]

# Section names to look for (case-insensitive)
SECTION_NAMES = {
    "experience": ["experience", "work experience", "employment", "professional experience"],
    "education": ["education", "academic", "qualification"],
    "skills": ["skills", "technical skills", "core competencies"]
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def allowed_file(filename):
    """Check if the file has an allowed extension."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return f".{ext}" in ALLOWED_EXTENSIONS


def extract_text_from_file(file_content, filename):
    """
    Extract text from uploaded file based on extension.
    file_content: bytes from request.files['resume'].read()
    filename: original filename for extension detection
    Returns: string of extracted text, or empty string on error.
    """
    ext = filename.rsplit(".", 1)[1].lower()

    if ext == "txt":
        try:
            return file_content.decode("utf-8", errors="replace")
        except Exception:
            return ""

    if ext == "docx":
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_content))
            paragraphs = []
            for para in doc.paragraphs:
                paragraphs.append(para.text)
            return "\n".join(paragraphs)
        except Exception:
            return ""

    if ext == "pdf":
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts)
        except Exception:
            return ""

    return ""


def _has_section(text_lower, section_keywords):
    """Check if text contains any of the given section keywords (e.g. 'experience')."""
    for keyword in section_keywords:
        if keyword in text_lower:
            return True
    return False


def _has_email(text):
    """Check if text contains something that looks like an email."""
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    return bool(re.search(pattern, text))


def _has_phone(text):
    """Check if text contains something that looks like a phone number."""
    pattern = r"[\d\-\(\)\s]{10,}"
    return bool(re.search(r"\d{3}[\s\-\.]?\d{3}[\s\-\.]?\d{4}", text))


def _has_bullet_points(text):
    """Check if text contains bullet points (•, -, *, etc.)."""
    bullets = ["•", "-", "*", "◦", "▪"]
    for bullet in bullets:
        if bullet in text:
            return True
    # Also check for lines that start with hyphen
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("-") and len(stripped) > 2:
            return True
    return False


def _count_action_verbs(text_lower):
    """Count how many action verbs appear in the text."""
    count = 0
    for verb in ACTION_VERBS:
        if verb in text_lower:
            count += 1
    return count


def _count_resume_keywords(text_lower):
    """Count how many resume keywords appear in the text."""
    count = 0
    for keyword in RESUME_KEYWORDS:
        if keyword in text_lower:
            count += 1
    return count


def analyze_resume(text):
    """
    Analyze resume text and return (score, tips).
    score: int 0-100
    tips: list of strings with improvement suggestions
    """
    if not text or not text.strip():
        return 0, ["Your resume appears to be empty. Please upload a file with content."]

    text_lower = text.lower().strip()
    words = text_lower.split()
    word_count = len(words)

    score = 0
    tips = []
    max_score = 100

    # Required sections (10 pts each, max 30)
    has_experience = _has_section(text_lower, SECTION_NAMES["experience"])
    has_education = _has_section(text_lower, SECTION_NAMES["education"])
    has_skills = _has_section(text_lower, SECTION_NAMES["skills"])

    if has_experience:
        score += 10
    else:
        tips.append("Add an Experience or Work Experience section.")

    if has_education:
        score += 10
    else:
        tips.append("Add an Education section.")

    if has_skills:
        score += 10
    else:
        tips.append("Add a Skills section highlighting your key competencies.")

    # Contact info (5 pts each, max 10)
    if _has_email(text):
        score += 5
    else:
        tips.append("Add your email address for contact.")

    if _has_phone(text):
        score += 5
    else:
        tips.append("Add your phone number for contact.")

    # Bullet points (5 pts)
    if _has_bullet_points(text):
        score += 5
    else:
        tips.append("Use bullet points to list achievements and responsibilities.")

    # Word count (10 pts) - ideal range 300-800
    if 300 <= word_count <= 800:
        score += 10
    elif 200 <= word_count < 300:
        score += 5
        tips.append("Consider adding more detail. A typical one-page resume has 300-800 words.")
    elif word_count < 200:
        tips.append("Your resume is quite short. Aim for 300-800 words for a one-page resume.")
    elif word_count > 1000:
        score += 5
        tips.append("Consider shortening your resume. Keep it concise (around 1-2 pages).")

    # Action verbs (15 pts max)
    verb_count = _count_action_verbs(text_lower)
    if verb_count >= 3:
        score += 15
    elif verb_count >= 1:
        score += 8
        tips.append("Include more action verbs like 'managed', 'led', 'developed', 'implemented'.")
    else:
        tips.append("Include action verbs like 'managed', 'led', 'developed', 'implemented' to strengthen your resume.")

    # Resume keywords (15 pts max)
    keyword_count = _count_resume_keywords(text_lower)
    if keyword_count >= 5:
        score += 15
    elif keyword_count >= 2:
        score += 8
        tips.append("Use keywords relevant to your industry (e.g., experience, team, results, achieved).")
    else:
        tips.append("Add industry-relevant keywords (experience, skills, team, results) to improve ATS compatibility.")

    # Cap score at 100
    score = min(score, max_score)

    if score >= 80 and not tips:
        tips.append("Great job! Your resume looks strong. Keep it updated as you gain experience.")

    return score, tips
