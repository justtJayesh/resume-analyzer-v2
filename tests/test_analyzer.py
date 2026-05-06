"""Tests for the analyzer module."""

import pytest
from analyzer import (
    analyze_resume,
    extract_text_from_file,
    allowed_file,
    ACTION_VERBS,
    RESUME_KEYWORDS,
)


class TestAllowedFile:
    def test_pdf_allowed(self):
        assert allowed_file("resume.pdf") is True

    def test_docx_allowed(self):
        assert allowed_file("resume.docx") is True

    def test_txt_allowed(self):
        assert allowed_file("resume.txt") is True

    def test_invalid_extension(self):
        assert allowed_file("resume.jpg") is False

    def test_no_extension(self):
        assert allowed_file("resume") is False


class TestAnalyzeResume:
    def test_empty_text(self):
        score, tips, detailed = analyze_resume("")
        assert score == 0
        assert "empty" in tips[0].lower()
        assert detailed == {}

    def test_good_resume(self):
        text = """
        John Doe
        john@email.com
        555-123-4567

        Experience
        - Managed a team of 5 developers
        - Led the implementation of new features
        - Developed REST APIs

        Education
        Bachelor of Science in Computer Science

        Skills
        Python, JavaScript, SQL
        """
        score, tips, detailed = analyze_resume(text)
        assert score > 0
        assert score <= 100
        assert isinstance(tips, list)
        assert isinstance(detailed, dict)

    def test_minimum_word_count(self):
        text = "a " * 200  # 200 words
        score, tips, _ = analyze_resume(text)
        assert score > 0

    def test_action_verbs_scored(self):
        text = f"""
        Experience
        - {ACTION_VERBS[0]} a team
        - {ACTION_VERBS[1]} new projects
        """
        score, tips, _ = analyze_resume(text)
        assert score > 0

    def test_returns_three_values(self):
        result = analyze_resume("some text")
        assert len(result) == 3, "analyze_resume must return (score, tips, detailed_results)"

    def test_detailed_results_structure(self):
        text = "Experience\nEducation\nSkills\njohn@email.com\n555-123-4567"
        _, _, detailed = analyze_resume(text)
        assert "score_breakdown" in detailed
        assert "skills_analysis" in detailed
        assert "ats_compatibility" in detailed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
