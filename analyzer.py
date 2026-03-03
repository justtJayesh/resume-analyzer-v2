"""Resume analyzer - extracts text and computes keyword-based score and tips."""

import re
import io
from typing import Dict, List, Tuple, Optional

# Action verbs for scoring
ACTION_VERBS = [
    "managed", "led", "developed", "implemented", "designed", "created",
    "improved", "analyzed", "coordinated", "executed", "built", "delivered",
    "achieved", "directed", "established", "facilitated", "generated", "optimized",
    "orchestrated", "spearheaded", "transformed", "validated", "monitored", "trained"
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

# Common hard skills (technical, job-specific)
HARD_SKILLS = [
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", "rust", "php", "swift", "kotlin",
    # Web Technologies
    "html", "css", "react", "angular", "vue", "node.js", "django", "flask", "spring", "asp.net",
    # Data & ML
    "sql", "machine learning", "deep learning", "data analysis", "data science", "pandas", "numpy",
    "tensorflow", "pytorch", "tableau", "power bi", "excel",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "ci/cd", "terraform",
    # Tools & Software
    "git", "github", "jira", "confluence", "figma", "sketch", "photoshop", "illustrator",
    # Project Management
    "agile", "scrum", "kanban", "jira", "project management", "product management",
    # Marketing & Digital
    "seo", "sem", "google analytics", "facebook ads", "content marketing", "email marketing",
    # Finance & Accounting
    "financial analysis", "budgeting", "forecasting", "auditing", "quickbooks", "sap",
    # Healthcare
    "emr", "ehr", "hipaa", "clinical trials", "patient care", "medical billing",
    # Other Technical
    "testing", "qa", "automation", "cybersecurity", "networking", "linux", "unix"
]

# Common soft skills
SOFT_SKILLS = [
    "leadership", "communication", "teamwork", "problem-solving", "analytical",
    "creativity", "adaptability", "time management", "organization", "collaboration",
    "attention to detail", "critical thinking", "decision making", "interpersonal",
    "presentation", "negotiation", "conflict resolution", "customer service",
    "mentoring", "strategic planning", "initiative", "multitasking", "self-motivated",
    "accountability", "flexibility", "responsibility", "dependability"
]

# Common degree keywords
DEGREE_KEYWORDS = [
    "bachelor", "master", "phd", "doctorate", "associate", "mba", "bs", "ba", "ms", "ma",
    "b.tech", "m.tech", "b.sc", "m.sc", "bca", "mca", "llb", "llm", "md", "do", "rn", "bsn"
]

# Job title keywords
JOB_TITLE_KEYWORDS = [
    "manager", "director", "engineer", "developer", "analyst", "consultant", "specialist",
    "coordinator", "administrator", "executive", "assistant", "associate", "lead", "senior",
    "junior", "intern", "principal", "architect", "designer", "technician"
]

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


def _extract_skills(text_lower) -> Tuple[List[str], List[str]]:
    """Extract hard and soft skills from text."""
    found_hard = []
    found_soft = []

    for skill in HARD_SKILLS:
        if skill in text_lower:
            found_hard.append(skill)

    for skill in SOFT_SKILLS:
        if skill in text_lower:
            found_soft.append(skill)

    return found_hard, found_soft


def _extract_degrees(text_lower) -> List[str]:
    """Extract degree mentions from text."""
    found = []
    for degree in DEGREE_KEYWORDS:
        if degree in text_lower:
            found.append(degree)
    return found


def _extract_job_titles(text_lower) -> List[str]:
    """Extract job title keywords from text."""
    found = []
    for title in JOB_TITLE_KEYWORDS:
        if title in text_lower:
            found.append(title)
    return found


def _calculate_skill_match(resume_skills: List[str], jd_skills: List[str]) -> Tuple[int, List[str]]:
    """Calculate skill match percentage and identify gaps."""
    if not jd_skills:
        return 0, []

    resume_skill_set = set(s.lower() for s in resume_skills)
    jd_skill_set = set(s.lower() for s in jd_skills)

    matched = resume_skill_set.intersection(jd_skill_set)
    missing = jd_skill_set - resume_skill_set

    match_percentage = int((len(matched) / len(jd_skill_set)) * 100) if jd_skill_set else 0

    return match_percentage, list(missing)


def _check_ats_compatibility(text: str) -> Dict[str, any]:
    """Check ATS (Applicant Tracking System) compatibility."""
    issues = []
    score = 100

    text_lower = text.lower()

    # Check for tables (ATS often can't read them)
    if "table" in text_lower or "column" in text_lower:
        issues.append("Avoid using tables - ATS systems may not parse them correctly.")
        score -= 10

    # Check for text boxes
    if "text box" in text_lower or "textbox" in text_lower:
        issues.append("Avoid text boxes - ATS cannot read them.")
        score -= 10

    # Check for headers/footers (ATS may miss them)
    has_header = bool(re.search(r'^\s*[\w\s]+\s*:\s*\S+', text, re.MULTILINE))
    if has_header:
        # Only warn if it looks like a header
        pass

    # Check for special characters that might cause issues
    special_chars = ["©", "®", "™", "°", "§", "¶"]
    for char in special_chars:
        if char in text:
            issues.append(f"Remove special characters like '{char}' - they can confuse ATS.")
            score -= 5

    # Check for all caps sections (ATS may skip)
    lines = text.split('\n')
    caps_lines = [line for line in lines if line.isupper() and len(line) > 10]
    if caps_lines:
        issues.append("Avoid using ALL CAPS - ATS may not recognize the text.")
        score -= 5

    # Check for graphics/images indicators
    if any(word in text_lower for word in ["image", "photo", "picture", "graphic"]):
        issues.append("Remove images and photos from your resume for better ATS parsing.")
        score -= 10

    # Check for proper email format
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    if not re.search(email_pattern, text):
        issues.append("Add a standard email address (e.g., name@domain.com).")
        score -= 10

    # Check for file size proxy (very long resumes)
    if len(text.split()) > 1000:
        issues.append("Your resume may be too long. Keep it under 2 pages for ATS.")
        score -= 5

    # Check for proper section headings
    has_proper_headings = False
    for section in SECTION_NAMES.values():
        if any(s in text_lower for s in section):
            has_proper_headings = True
            break

    if not has_proper_headings:
        issues.append("Use clear section headings (Experience, Education, Skills) for ATS.")
        score -= 10

    score = max(score, 0)

    return {
        "score": score,
        "issues": issues,
        "recommendations": [] if score >= 80 else [
            "Use a clean, simple format",
            "Save as .docx or .pdf (not scanned)",
            "Use standard section headings"
        ]
    }


def _check_formatting_tips(text: str) -> List[str]:
    """Provide formatting and design tips."""
    tips = []

    # Check line length
    lines = text.split('\n')
    long_lines = [len(line) for line in lines if len(line) > 80]
    if long_lines and max(long_lines) > 100:
        tips.append("Some lines are very long. Keep lines under 80 characters for readability.")

    # Check for consistent spacing
    if '  ' in text:
        tips.append("Remove extra spaces between words.")

    # Check bullet consistency
    bullet_types = set()
    for line in lines:
        if line.strip().startswith('•'):
            bullet_types.add('•')
        elif line.strip().startswith('-'):
            bullet_types.add('-')
        elif line.strip().startswith('*'):
            bullet_types.add('*')

    if len(bullet_types) > 1:
        tips.append("Use consistent bullet points throughout your resume.")

    # Check for proper date formats
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
        r'[A-Za-z]{3,9}\s+\d{4}',     # Month YYYY
    ]
    has_dates = any(re.search(p, text) for p in date_patterns)
    if not has_dates:
        tips.append("Include dates for your work experience and education (e.g., Jan 2020 - Present).")

    # Check for quantifiable achievements
    numbers_count = len(re.findall(r'\d+%|\$\d+|\d{3,}', text))
    if numbers_count < 3:
        tips.append("Add quantifiable achievements (e.g., 'Increased sales by 25%', 'Managed team of 10').")

    return tips


def _compare_with_job_description(resume_text: str, job_description: str) -> Dict[str, any]:
    """Compare resume with job description and provide match analysis."""
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    # Extract skills from both
    resume_hard, resume_soft = _extract_skills(resume_lower)
    jd_hard, jd_soft = _extract_skills(jd_lower)

    # Calculate matches
    hard_skill_match, hard_skill_gaps = _calculate_skill_match(resume_hard, jd_hard)
    soft_skill_match, soft_skill_gaps = _calculate_skill_match(resume_soft, jd_soft)

    # Extract and compare degrees
    resume_degrees = _extract_degrees(resume_lower)
    jd_degrees = _extract_degrees(jd_lower)
    degree_match = bool(set(r.lower() for r in resume_degrees).intersection(set(d.lower() for d in jd_degrees)))

    # Extract and compare job titles
    resume_titles = _extract_job_titles(resume_lower)
    jd_titles = _extract_job_titles(jd_lower)
    title_match = bool(set(r.lower() for r in resume_titles).intersection(set(t.lower() for t in jd_titles)))

    # Extract other keywords from JD
    jd_keywords = set()
    common_words = {'and', 'the', 'is', 'are', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'you', 'your', 'we', 'our', 'us', 'this', 'that', 'be', 'have', 'has', 'had', 'it', 'from', 'or', 'as', 'but', 'not', 'they', 'their', 'will', 'can', 'may', 'should', 'could', 'would'}
    for word in jd_lower.split():
        word = word.strip('.,;:!()[]{}')
        if len(word) > 3 and word not in common_words:
            jd_keywords.add(word)

    resume_keywords = set()
    for word in resume_lower.split():
        word = word.strip('.,;:!()[]{}')
        if len(word) > 3 and word not in common_words:
            resume_keywords.add(word)

    other_match = len(resume_keywords.intersection(jd_keywords))
    other_total = len(jd_keywords)
    other_match_pct = int((other_match / other_total) * 100) if other_total > 0 else 0

    # Calculate overall match score
    weights = {
        'hard_skill': 0.30,
        'soft_skill': 0.20,
        'degree': 0.15,
        'title': 0.15,
        'other': 0.20
    }

    overall_match = int(
        hard_skill_match * weights['hard_skill'] +
        soft_skill_match * weights['soft_skill'] +
        (100 if degree_match else 0) * weights['degree'] +
        (100 if title_match else 0) * weights['title'] +
        other_match_pct * weights['other']
    )

    return {
        "overall_match": overall_match,
        "hard_skill_match": hard_skill_match,
        "hard_skill_gaps": hard_skill_gaps[:10],  # Limit to top 10
        "soft_skill_match": soft_skill_match,
        "soft_skill_gaps": soft_skill_gaps[:10],
        "degree_match": degree_match,
        "degree_found": resume_degrees,
        "title_match": title_match,
        "title_found": resume_titles,
        "other_keyword_match": other_match_pct,
        "jd_keywords_matched": list(resume_keywords.intersection(jd_keywords))[:20]
    }


def analyze_resume(text: str, job_description: str = None) -> Tuple[int, List[str], Dict[str, any]]:
    """
    Analyze resume text and return (score, tips, detailed_results).
    score: int 0-100
    tips: list of strings with improvement suggestions
    detailed_results: dict with breakdown of all analysis components

    If job_description is provided, also performs JD-based comparison.
    """
    if not text or not text.strip():
        return 0, ["Your resume appears to be empty. Please upload a file with content."], {}

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

    # Extract skills for detailed results
    resume_hard_skills, resume_soft_skills = _extract_skills(text_lower)

    # Cap score at 100
    score = min(score, max_score)

    # Get ATS compatibility
    ats_result = _check_ats_compatibility(text)

    # Get formatting tips
    formatting_tips = _check_formatting_tips(text)

    # Add ATS issues to tips
    for issue in ats_result.get('issues', []):
        tips.append(issue)

    # Add formatting tips
    tips.extend(formatting_tips)

    # Build detailed results
    detailed_results = {
        "score_breakdown": {
            "overall_score": score,
            "sections": {
                "experience": has_experience,
                "education": has_education,
                "skills": has_skills
            },
            "contact": {
                "email": _has_email(text),
                "phone": _has_phone(text)
            },
            "formatting": {
                "bullet_points": _has_bullet_points(text),
                "word_count": word_count
            },
            "content": {
                "action_verbs": verb_count,
                "keywords": keyword_count
            }
        },
        "skills_analysis": {
            "hard_skills_found": resume_hard_skills,
            "soft_skills_found": resume_soft_skills,
            "hard_skills_count": len(resume_hard_skills),
            "soft_skills_count": len(resume_soft_skills)
        },
        "ats_compatibility": ats_result,
        "formatting_tips": formatting_tips
    }

    # If job description provided, add JD comparison
    if job_description and job_description.strip():
        jd_comparison = _compare_with_job_description(text, job_description)
        detailed_results["job_match"] = jd_comparison
        detailed_results["score_breakdown"]["jd_match_score"] = jd_comparison["overall_match"]

        # Add JD-specific tips
        if jd_comparison["hard_skill_gaps"]:
            tips.append(f"Add these hard skills from the job description: {', '.join(jd_comparison['hard_skill_gaps'][:5])}")

        if jd_comparison["soft_skill_gaps"]:
            tips.append(f"Consider highlighting these soft skills: {', '.join(jd_comparison['soft_skill_gaps'][:5])}")

        if not jd_comparison["degree_match"]:
            tips.append("The job description mentions degree requirements not found in your resume.")

        if not jd_comparison["title_match"]:
            tips.append("Consider aligning your job titles with those in the job description.")

        if jd_comparison["overall_match"] < 50:
            tips.append(f"Your resume matches only {jd_comparison['overall_match']}% of the job description. Review the JD and add relevant keywords.")
        elif jd_comparison["overall_match"] >= 70:
            tips.append(f"Great match! Your resume covers {jd_comparison['overall_match']}% of the job requirements.")

    if score >= 80 and not tips:
        tips.append("Great job! Your resume looks strong. Keep it updated as you gain experience.")

    return score, tips, detailed_results
