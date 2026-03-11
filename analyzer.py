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

# Power words that make resumes impactful
POWER_WORDS = [
    "achieved", "accelerated", "accomplished", "advanced", "analyzed", "architected",
    "audited", "automated", "built", "calculated", "collaborated", "created", "delivered",
    "designed", "developed", "directed", "eliminated", "enhanced", "established", "executed",
    "expanded", "facilitated", "founded", "generated", "implemented", "improved", "increased",
    "influenced", "innovated", "launched", "led", "managed", "negotiated", "optimized",
    "orchestrated", "oversaw", "pioneered", "planned", "reduced", "resolved", "spearheaded",
    "streamlined", "structured", "succeeded", "transformed", "validated", "volunteered"
]

# Important resume keywords by category
RESUME_KEYWORDS_BY_CATEGORY = {
    "achievements": ["achieved", "accomplished", "awarded", "champion", "conquer", "delivered",
                     "exceeded", "honored", "impact", "improved", "increased", "outperformed",
                     "recognition", "record", "reduced", "saved", "solved", "transformed", "won"],
    "skills": ["abilities", "capabilities", "competencies", "expertise", "proficient", "skilled",
               "specialized", "trained", "versed"],
    "leadership": ["lead", "manage", "mentor", "direct", "coordinate", "supervise", "oversee",
                   "guide", "coach", "team", "collaborate", "influence"],
    "results": ["results", "impact", "outcome", "performance", "metrics", "data", "analytics",
               "roi", "revenue", "growth", "efficiency", "productivity"]
}

# Ideal resume benchmarks
IDEAL_BENCHMARKS = {
    "word_count": {"min": 300, "ideal": 500, "max": 800},
    "hard_skills": {"min": 3, "ideal": 8, "max": 20},
    "soft_skills": {"min": 2, "ideal": 5, "max": 10},
    "action_verbs": {"min": 3, "ideal": 8, "max": 15},
    "bullet_points": {"min": 5, "ideal": 15, "max": 30},
    "quantifiable_achievements": {"min": 2, "ideal": 5, "max": 15}
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


def _analyze_text_statistics(text: str) -> Dict[str, any]:
    """Extract comprehensive text statistics."""
    words = text.split()
    char_count = len(text)
    char_count_no_spaces = len(text.replace(" ", ""))
    line_count = len(text.split("\n"))
    paragraph_count = len([p for p in text.split("\n\n") if p.strip()])
    sentence_count = len(re.findall(r'[.!?]+', text)) or 1
    word_count = len(words)

    # Average calculations
    avg_word_length = char_count_no_spaces / word_count if word_count > 0 else 0
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

    # Readability estimate (simplified Flesch-Kincaid)
    # Higher score = more readable
    syllables = sum(1 for char in text.lower() if char in 'aeiou')
    if word_count > 0 and sentence_count > 0:
        readability = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllables / word_count)
        readability = max(0, min(100, readability))
    else:
        readability = 50

    # Page estimation (assuming ~500 words per page, standard margins)
    if word_count <= 300:
        pages = 1
    elif word_count <= 600:
        pages = 1.5
    elif word_count <= 900:
        pages = 2
    else:
        pages = round(word_count / 500, 1)

    # Count bullet points
    bullet_count = len(re.findall(r'^[\s]*[•\-\*◦▪]', text, re.MULTILINE))

    # Count quantifiable achievements (numbers, percentages, currency)
    quantifiable_count = len(re.findall(r'\d+%|\$\d+|\d+\s*(year|month|day|hour)|'
                                          r'\d+\s*(people|team|member|client|customer)|'
                                          r'\d+x|\d+[\s,-]\d+', text.lower()))

    return {
        "word_count": word_count,
        "character_count": char_count,
        "character_count_no_spaces": char_count_no_spaces,
        "line_count": line_count,
        "paragraph_count": paragraph_count,
        "sentence_count": sentence_count,
        "average_word_length": round(avg_word_length, 1),
        "average_sentence_length": round(avg_sentence_length, 1),
        "readability_score": round(readability, 1),
        "page_estimate": pages,
        "bullet_count": bullet_count,
        "quantifiable_achievements": quantifiable_count
    }


def _extract_keywords_with_frequency(text_lower: str, top_n: int = 20) -> List[Dict[str, any]]:
    """Extract keywords with their frequency/density."""
    common_words = {'and', 'the', 'is', 'are', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of',
                    'with', 'by', 'you', 'your', 'we', 'our', 'us', 'this', 'that', 'be', 'have',
                    'has', 'had', 'it', 'from', 'or', 'as', 'but', 'not', 'they', 'their', 'will',
                    'can', 'may', 'should', 'could', 'would', 'my', 'me', 'i', 'am', 'was', 'were',
                    'been', 'being', 'do', 'does', 'did', 'doing', 'so', 'if', 'than', 'then',
                    'when', 'where', 'which', 'who', 'what', 'how', 'all', 'any', 'some', 'no',
                    'more', 'most', 'other', 'such', 'only', 'own', 'same', 'too', 'very', 'just',
                    'also', 'now', 'here', 'there', 'because', 'before', 'after', 'above', 'below',
                    'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'once'}

    words = text_lower.split()
    word_freq = {}

    for word in words:
        word = word.strip('.,;:!()[]{}"\'-')
        if len(word) > 2 and word not in common_words:
            word_freq[word] = word_freq.get(word, 0) + 1

    total_words = len(words) if words else 1
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return [{"word": word, "count": count, "density": round(count / total_words * 100, 2)}
            for word, count in sorted_words]


def _extract_action_verbs_details(text_lower: str) -> Dict[str, any]:
    """Extract detailed action verb analysis."""
    found_verbs = []
    for verb in ACTION_VERBS:
        if verb in text_lower:
            found_verbs.append(verb)

    # Check power words
    found_power_words = []
    for word in POWER_WORDS:
        if word in text_lower:
            found_power_words.append(word)

    return {
        "action_verbs_found": found_verbs,
        "action_verb_count": len(found_verbs),
        "power_words_found": found_power_words,
        "power_word_count": len(found_power_words)
    }


def _analyze_header_section(text: str) -> Dict[str, any]:
    """Analyze the header/contact information section."""
    has_email = _has_email(text)
    has_phone = _has_phone(text)

    # Check for LinkedIn
    linkedin_pattern = r'linkedin\.com/(in/)?[a-zA-Z0-9-]+'
    has_linkedin = bool(re.search(linkedin_pattern, text.lower()))

    # Check for location/address
    location_pattern = r'(?:location|address|city|street)[\s:]+[a-zA-Z\s,]+'
    has_location = bool(re.search(location_pattern, text.lower()))

    # Check for website/portfolio
    website_pattern = r'(?:www\.|portfolio|github\.com|gitlab\.com|bitbucket\.org)[a-zA-Z0-9./\-]+'
    has_website = bool(re.search(website_pattern, text.lower()))

    # Try to extract name (usually at the top, often in all caps or title case)
    lines = text.split("\n")
    potential_name = ""
    if lines:
        first_line = lines[0].strip()
        if 2 <= len(first_line.split()) <= 4:
            # Likely a name if it's short and not containing common words
            if not any(w in first_line.lower() for w in ['resume', 'cv', 'curriculum']):
                potential_name = first_line

    contact_score = sum([has_email, has_phone, has_linkedin, has_location, has_website])

    return {
        "has_email": has_email,
        "has_phone": has_phone,
        "has_linkedin": has_linkedin,
        "has_location": has_location,
        "has_website": has_website,
        "potential_name": potential_name,
        "contact_score": contact_score,
        "total_contact_fields": 5
    }


def _analyze_summary_section(text_lower: str) -> Dict[str, any]:
    """Analyze summary/objective section."""
    summary_keywords = ["summary", "objective", "profile", "about", "overview", "introduction"]
    has_summary = any(kw in text_lower for kw in summary_keywords)

    # Check for summary quality indicators
    has_summary_text = False
    summary_length = 0

    if has_summary:
        # Find text near summary keyword
        for keyword in summary_keywords:
            pattern = rf'{keyword}[:\s]*(.{{50,200}}(?:\.|$))'
            match = re.search(pattern, text_lower)
            if match:
                has_summary_text = True
                summary_length = len(match.group(1))
                break

    return {
        "has_summary": has_summary and has_summary_text,
        "summary_length": summary_length,
        "has_professional_summary": has_summary_text and summary_length > 50
    }


def _analyze_section_quality(text: str, text_lower: str) -> Dict[str, any]:
    """Analyze quality of each resume section."""
    sections = {
        "experience": ["experience", "work experience", "employment", "professional experience",
                       "work history", "career"],
        "education": ["education", "academic", "qualification", "degree", "university", "college"],
        "skills": ["skills", "technical skills", "core competencies", "competencies", "expertise"],
        "projects": ["project", "projects", "portfolio"],
        "certifications": ["certification", "certifications", "certificate", "licenses", "license"]
    }

    section_analysis = {}

    for section_name, keywords in sections.items():
        has_section = any(kw in text_lower for kw in keywords)
        section_analysis[section_name] = {
            "present": has_section,
            "quality_score": 0
        }

        if has_section:
            # Check quality indicators for experience section
            if section_name == "experience":
                # Check for bullet points in experience
                exp_lines = [line for line in text.split("\n")
                            if any(kw in line.lower() for kw in keywords[:3])]
                has_bullets = any("•" in line or "-" in line for line in exp_lines)
                has_dates = bool(re.search(r'\d{4}|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', text_lower))
                section_analysis[section_name]["quality_score"] = (
                    (1 if has_bullets else 0) * 5 +
                    (1 if has_dates else 0) * 5
                )

            # Check for skills section quality
            elif section_name == "skills":
                hard, soft = _extract_skills(text_lower)
                section_analysis[section_name]["quality_score"] = min(10, len(hard) + len(soft))

            # Education quality
            elif section_name == "education":
                degrees = _extract_degrees(text_lower)
                section_analysis[section_name]["quality_score"] = min(10, len(degrees) * 5)

    return section_analysis


def _identify_strengths_and_weaknesses(text: str, text_lower: str,
                                         score_breakdown: Dict) -> Tuple[List[str], List[Dict[str, str]]]:
    """Identify strengths and weaknesses based on analysis."""
    strengths = []
    weaknesses = []

    # Check strengths
    if score_breakdown.get("sections", {}).get("experience"):
        strengths.append("Has clear Experience section")

    if score_breakdown.get("sections", {}).get("education"):
        strengths.append("Has Education section")

    if score_breakdown.get("sections", {}).get("skills"):
        strengths.append("Has Skills section")

    if score_breakdown.get("contact", {}).get("email"):
        strengths.append("Email address provided")

    if score_breakdown.get("contact", {}).get("phone"):
        strengths.append("Phone number provided")

    if score_breakdown.get("formatting", {}).get("bullet_points"):
        strengths.append("Uses bullet points for readability")

    if score_breakdown.get("content", {}).get("action_verbs", 0) >= 3:
        strengths.append("Strong action verb usage")

    hard_skills, soft_skills = _extract_skills(text_lower)
    if len(hard_skills) >= 5:
        strengths.append(f"Good range of hard skills ({len(hard_skills)} found)")

    if len(soft_skills) >= 3:
        strengths.append(f"Good soft skills presentation ({len(soft_skills)} found)")

    # Check weaknesses with priority
    stats = _analyze_text_statistics(text)

    if stats["word_count"] < 300:
        weaknesses.append({
            "priority": "high",
            "issue": f"Resume is too short ({stats['word_count']} words)",
            "suggestion": "Aim for 300-800 words for a comprehensive resume"
        })

    if stats["quantifiable_achievements"] < 2:
        weaknesses.append({
            "priority": "high",
            "issue": "Few quantifiable achievements",
            "suggestion": "Add numbers, percentages, and metrics to demonstrate impact"
        })

    if not score_breakdown.get("contact", {}).get("email"):
        weaknesses.append({
            "priority": "high",
            "issue": "Missing email address",
            "suggestion": "Add a professional email address"
        })

    if not score_breakdown.get("contact", {}).get("phone"):
        weaknesses.append({
            "priority": "medium",
            "issue": "Missing phone number",
            "suggestion": "Add a contact phone number"
        })

    if not score_breakdown.get("formatting", {}).get("bullet_points"):
        weaknesses.append({
            "priority": "medium",
            "issue": "No bullet points found",
            "suggestion": "Use bullet points to list achievements and responsibilities"
        })

    if score_breakdown.get("content", {}).get("action_verbs", 0) < 3:
        weaknesses.append({
            "priority": "medium",
            "issue": "Limited action verbs",
            "suggestion": "Use more action verbs like led, managed, developed, implemented"
        })

    if stats["readability_score"] < 40:
        weaknesses.append({
            "priority": "low",
            "issue": "Low readability score",
            "suggestion": "Simplify sentences and use shorter paragraphs"
        })

    if len(hard_skills) < 3:
        weaknesses.append({
            "priority": "medium",
            "issue": "Limited technical skills identified",
            "suggestion": "Add more relevant technical skills"
        })

    return strengths, weaknesses


def _analyze_ats_detailed(text: str) -> Dict[str, any]:
    """Enhanced ATS analysis with detailed issues."""
    base_ats = _check_ats_compatibility(text)
    detailed_issues = []

    text_lower = text.lower()
    issues_by_severity = {"critical": [], "high": [], "medium": [], "low": []}

    # Critical issues
    if not _has_email(text):
        issues_by_severity["critical"].append({
            "issue": "No email address found",
            "impact": "Recruiters cannot contact you",
            "fix": "Add a professional email address"
        })

    # High severity
    if len(text.split()) > 1000:
        issues_by_severity["high"].append({
            "issue": "Resume too long",
            "impact": "May be truncated by ATS or skipped by recruiters",
            "fix": "Keep resume under 2 pages"
        })

    # Check for problematic formats
    if re.search(r'[©®™°§¶]', text):
        issues_by_severity["high"].append({
            "issue": "Special characters detected",
            "impact": "May cause parsing errors in ATS",
            "fix": "Remove special characters"
        })

    # Medium severity
    if not _has_bullet_points(text):
        issues_by_severity["medium"].append({
            "issue": "No bullet points used",
            "impact": "Harder to scan, may lose important details",
            "fix": "Use bullet points for achievements"
        })

    # Check for consistent date formats
    date_formats = set()
    for match in re.finditer(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|([A-Za-z]+\s+\d{4})|(\d{4}\s*-\s*\d{4})', text):
        date_formats.add(match.group(0))

    if len(date_formats) > 1:
        issues_by_severity["medium"].append({
            "issue": "Inconsistent date formats",
            "impact": "May confuse ATS parsing",
            "fix": "Use consistent date format throughout"
        })

    # Check for graphics/images references
    if any(word in text_lower for word in ["image", "photo", "picture", "graphic"]):
        issues_by_severity["high"].append({
            "issue": "References to images/graphics",
            "impact": "ATS cannot read images",
            "fix": "Remove all image references"
        })

    # Low severity issues
    lines = text.split('\n')
    if any(line.isupper() and len(line) > 10 for line in lines):
        issues_by_severity["low"].append({
            "issue": "All caps text detected",
            "impact": "May be harder to read",
            "fix": "Use title case instead of ALL CAPS"
        })

    return {
        "score": base_ats["score"],
        "issues": base_ats["issues"],
        "issues_by_severity": issues_by_severity,
        "recommendations": base_ats.get("recommendations", []),
        "file_format_tip": "Save as .docx or PDF (not scanned)"
    }


def _compare_with_benchmarks(text: str, text_lower: str) -> Dict[str, any]:
    """Compare resume metrics with ideal benchmarks."""
    stats = _analyze_text_statistics(text)
    hard_skills, soft_skills = _extract_skills(text_lower)
    verbs = _extract_action_verbs_details(text_lower)

    comparisons = {}

    # Word count comparison
    wc = stats["word_count"]
    if wc < IDEAL_BENCHMARKS["word_count"]["min"]:
        comparisons["word_count"] = {"status": "low", "actual": wc, "ideal": "300-800", "score": 30}
    elif wc > IDEAL_BENCHMARKS["word_count"]["max"]:
        comparisons["word_count"] = {"status": "high", "actual": wc, "ideal": "300-800", "score": 50}
    else:
        comparisons["word_count"] = {"status": "good", "actual": wc, "ideal": "300-800", "score": 100}

    # Hard skills comparison
    hs_count = len(hard_skills)
    if hs_count < IDEAL_BENCHMARKS["hard_skills"]["min"]:
        comparisons["hard_skills"] = {"status": "low", "actual": hs_count, "ideal": "8+", "score": 30}
    elif hs_count > IDEAL_BENCHMARKS["hard_skills"]["max"]:
        comparisons["hard_skills"] = {"status": "high", "actual": hs_count, "ideal": "8+", "score": 70}
    else:
        comparisons["hard_skills"] = {"status": "good", "actual": hs_count, "ideal": "8+", "score": 100}

    # Soft skills comparison
    ss_count = len(soft_skills)
    if ss_count < IDEAL_BENCHMARKS["soft_skills"]["min"]:
        comparisons["soft_skills"] = {"status": "low", "actual": ss_count, "ideal": "5+", "score": 30}
    else:
        comparisons["soft_skills"] = {"status": "good", "actual": ss_count, "ideal": "5+", "score": 100}

    # Action verbs comparison
    verb_count = verbs["action_verb_count"]
    if verb_count < IDEAL_BENCHMARKS["action_verbs"]["min"]:
        comparisons["action_verbs"] = {"status": "low", "actual": verb_count, "ideal": "8+", "score": 30}
    else:
        comparisons["action_verbs"] = {"status": "good", "actual": verb_count, "ideal": "8+", "score": 100}

    # Bullet points comparison
    bullet_count = stats["bullet_count"]
    if bullet_count < IDEAL_BENCHMARKS["bullet_points"]["min"]:
        comparisons["bullet_points"] = {"status": "low", "actual": bullet_count, "ideal": "15+", "score": 30}
    else:
        comparisons["bullet_points"] = {"status": "good", "actual": bullet_count, "ideal": "15+", "score": 100}

    # Quantifiable achievements
    quant_count = stats["quantifiable_achievements"]
    if quant_count < IDEAL_BENCHMARKS["quantifiable_achievements"]["min"]:
        comparisons["quantifiable_achievements"] = {"status": "low", "actual": quant_count, "ideal": "5+", "score": 30}
    else:
        comparisons["quantifiable_achievements"] = {"status": "good", "actual": quant_count, "ideal": "5+", "score": 100}

    return comparisons


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

    # Get enhanced analysis data
    text_stats = _analyze_text_statistics(text)
    keywords_freq = _extract_keywords_with_frequency(text_lower)
    verb_details = _extract_action_verbs_details(text_lower)
    header_analysis = _analyze_header_section(text)
    summary_analysis = _analyze_summary_section(text_lower)
    section_quality = _analyze_section_quality(text, text_lower)
    strengths, weaknesses = _identify_strengths_and_weaknesses(text, text_lower, {
        "sections": {"experience": has_experience, "education": has_education, "skills": has_skills},
        "contact": {"email": _has_email(text), "phone": _has_phone(text)},
        "formatting": {"bullet_points": _has_bullet_points(text)},
        "content": {"action_verbs": verb_count}
    })
    ats_detailed = _analyze_ats_detailed(text)
    benchmarks = _compare_with_benchmarks(text, text_lower)

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
            },
            # Score breakdown by category
            "scoring": {
                "sections_score": 30 if (has_experience and has_education and has_skills) else (20 if sum([has_experience, has_education, has_skills]) >= 2 else 10 if sum([has_experience, has_education, has_skills]) == 1 else 0),
                "contact_score": 10 if (_has_email(text) and _has_phone(text)) else (5 if (_has_email(text) or _has_phone(text)) else 0),
                "formatting_score": 5 if _has_bullet_points(text) else 0,
                "content_score": min(25, 10 + min(verb_count * 3, 15)),
                "keywords_score": min(15, keyword_count * 3),
                "ats_score": ats_detailed["score"] * 20 // 100
            }
        },
        "skills_analysis": {
            "hard_skills_found": resume_hard_skills,
            "soft_skills_found": resume_soft_skills,
            "hard_skills_count": len(resume_hard_skills),
            "soft_skills_count": len(resume_soft_skills)
        },
        "text_statistics": text_stats,
        "keyword_analysis": {
            "top_keywords": keywords_freq,
            "action_verbs_detail": verb_details
        },
        "header_analysis": header_analysis,
        "summary_analysis": summary_analysis,
        "section_quality": section_quality,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "ats_compatibility": ats_detailed,
        "formatting_tips": formatting_tips,
        "benchmarks": benchmarks
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
