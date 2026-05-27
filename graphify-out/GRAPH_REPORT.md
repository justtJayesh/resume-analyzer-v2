# Graph Report - .  (2026-05-06)

## Corpus Check
- Corpus is ~20,530 words - fits in a single context window. You may not need a graph.

## Summary
- 173 nodes · 299 edges · 15 communities detected
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 61 edges (avg confidence: 0.8)
- Token cost: 8,500 input · 2,800 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Auth & Feedback API|Auth & Feedback API]]
- [[_COMMUNITY_Route Handlers & Session|Route Handlers & Session]]
- [[_COMMUNITY_Text Extraction Layer|Text Extraction Layer]]
- [[_COMMUNITY_Resume Scoring Engine|Resume Scoring Engine]]
- [[_COMMUNITY_Job Description Matching|Job Description Matching]]
- [[_COMMUNITY_Keyword & Formatting Checks|Keyword & Formatting Checks]]
- [[_COMMUNITY_File Validation & Tests|File Validation & Tests]]
- [[_COMMUNITY_Analysis Orchestration|Analysis Orchestration]]
- [[_COMMUNITY_Statistics & Benchmarks|Statistics & Benchmarks]]
- [[_COMMUNITY_Contact Info Detection|Contact Info Detection]]
- [[_COMMUNITY_ATS Compatibility Checks|ATS Compatibility Checks]]
- [[_COMMUNITY_Database Initialization|Database Initialization]]
- [[_COMMUNITY_Project Documentation|Project Documentation]]
- [[_COMMUNITY_DB Test Fixtures|DB Test Fixtures]]
- [[_COMMUNITY_Agent Configuration|Agent Configuration]]

## God Nodes (most connected - your core abstractions)
1. `analyze_resume()` - 26 edges
2. `TestDatabase` - 19 edges
3. `analyze_resume` - 15 edges
4. `add_user()` - 14 edges
5. `home()` - 14 edges
6. `add_analysis()` - 12 edges
7. `get_connection()` - 11 edges
8. `update_feedback()` - 10 edges
9. `register()` - 10 edges
10. `get_analysis_by_id()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `home()` --references--> `home.html template`  [EXTRACTED]
  /Users/jayeshmate/Desktop/resume-analyzer-v2/.claude/worktrees/determined-noether-6fb16e/app.py → templates/home.html
- `analysis()` --references--> `analysis.html template`  [EXTRACTED]
  /Users/jayeshmate/Desktop/resume-analyzer-v2/.claude/worktrees/determined-noether-6fb16e/app.py → templates/analysis.html
- `login()` --references--> `auth.html template`  [EXTRACTED]
  /Users/jayeshmate/Desktop/resume-analyzer-v2/.claude/worktrees/determined-noether-6fb16e/app.py → templates/auth.html
- `register()` --references--> `auth.html template`  [EXTRACTED]
  /Users/jayeshmate/Desktop/resume-analyzer-v2/.claude/worktrees/determined-noether-6fb16e/app.py → templates/auth.html
- `home()` --calls--> `allowed_file`  [EXTRACTED]
  /Users/jayeshmate/Desktop/resume-analyzer-v2/.claude/worktrees/determined-noether-6fb16e/app.py → analyzer.py

## Hyperedges (group relationships)
- **Resume Analysis Pipeline** — analyzer_extracttextfromfile, analyzer_analyzeresume, database_addanalysis [EXTRACTED 0.95]
- **User Authentication Flow** — app_login, app_register, database_adduser, database_getuserbyusername [EXTRACTED 0.90]
- **Feedback Submission Flow** — app_submitfeedback, database_getanalysisbyid, database_updatefeedback [EXTRACTED 0.95]

## Communities

### Community 0 - "Auth & Feedback API"
Cohesion: 0.11
Nodes (26): Submit feedback (star rating + optional comment) for an analysis., submit_feedback(), add_analysis(), add_user(), delete_analysis(), get_analyses_by_user(), get_analysis_by_id(), get_connection() (+18 more)

### Community 1 - "Route Handlers & Session"
Cohesion: 0.11
Nodes (22): analysis_detail(), delete_analysis(), index(), login(), login_required(), Delete a specific analysis., Decorator to require login for a route. Returns JSON 401 for AJAX requests., Analysis detail page - shows full details of a specific analysis. (+14 more)

### Community 2 - "Text Extraction Layer"
Cohesion: 0.13
Nodes (19): extract_text_from_file(), extract_text_from_file, Extract text from uploaded file based on extension.     file_content: bytes from, analysis(), analysis_detail route, delete_analysis route, home(), login_required decorator (+11 more)

### Community 3 - "Resume Scoring Engine"
Cohesion: 0.17
Nodes (18): _analyze_ats_detailed, _analyze_header_section, analyze_resume, _analyze_section_quality, _analyze_summary_section, _analyze_text_statistics, _calculate_skill_match, _check_ats_compatibility (+10 more)

### Community 4 - "Job Description Matching"
Cohesion: 0.18
Nodes (12): _analyze_section_quality(), _calculate_skill_match(), _compare_with_job_description(), _extract_degrees(), _extract_job_titles(), _extract_skills(), Extract hard and soft skills from text., Extract degree mentions from text. (+4 more)

### Community 5 - "Keyword & Formatting Checks"
Cohesion: 0.17
Nodes (11): _check_formatting_tips(), _count_action_verbs(), _count_resume_keywords(), _extract_keywords_with_frequency(), _has_section(), Resume analyzer - extracts text and computes keyword-based score and tips., Check if text contains any of the given section keywords (e.g. 'experience')., Count how many action verbs appear in the text. (+3 more)

### Community 6 - "File Validation & Tests"
Cohesion: 0.25
Nodes (5): allowed_file(), allowed_file, Check if the file has an allowed extension., Tests for the analyzer module., TestAllowedFile

### Community 7 - "Analysis Orchestration"
Cohesion: 0.31
Nodes (5): analyze_resume(), _analyze_summary_section(), Analyze summary/objective section., Analyze resume text and return (score, tips, detailed_results).     score: int 0, TestAnalyzeResume

### Community 8 - "Statistics & Benchmarks"
Cohesion: 0.25
Nodes (8): _analyze_text_statistics(), _compare_with_benchmarks(), _extract_action_verbs_details(), _identify_strengths_and_weaknesses(), Extract comprehensive text statistics., Extract detailed action verb analysis., Identify strengths and weaknesses based on analysis., Compare resume metrics with ideal benchmarks.

### Community 9 - "Contact Info Detection"
Cohesion: 0.33
Nodes (6): _analyze_header_section(), _has_email(), _has_phone(), Check if text contains something that looks like an email., Check if text contains something that looks like a phone number., Analyze the header/contact information section.

### Community 10 - "ATS Compatibility Checks"
Cohesion: 0.33
Nodes (6): _analyze_ats_detailed(), _check_ats_compatibility(), _has_bullet_points(), Check if text contains bullet points (•, -, *, etc.)., Check ATS (Applicant Tracking System) compatibility., Enhanced ATS analysis with detailed issues.

### Community 11 - "Database Initialization"
Cohesion: 0.4
Nodes (4): init_db(), Create the database and tables if they do not exist., Tests for the database module., setup()

### Community 12 - "Project Documentation"
Cohesion: 1.0
Nodes (2): CVNest Project Memory, CVNest Project Overview

### Community 13 - "DB Test Fixtures"
Cohesion: 1.0
Nodes (1): Use temporary database for tests.

### Community 15 - "Agent Configuration"
Cohesion: 1.0
Nodes (1): Codex Agent Rules

## Knowledge Gaps
- **63 isolated node(s):** `SQLite database setup and helper functions for the resume analyzer app.`, `Return the path to the SQLite database file.`, `Create the database and tables if they do not exist.`, `Context manager for database connections.`, `Add a new user to the database.     Returns the user id on success, None if user` (+58 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Project Documentation`** (2 nodes): `CVNest Project Memory`, `CVNest Project Overview`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `DB Test Fixtures`** (1 nodes): `Use temporary database for tests.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Agent Configuration`** (1 nodes): `Codex Agent Rules`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `home()` connect `Text Extraction Layer` to `Auth & Feedback API`, `Route Handlers & Session`, `Resume Scoring Engine`, `File Validation & Tests`, `Analysis Orchestration`?**
  _High betweenness centrality (0.595) - this node is a cross-community bridge._
- **Why does `analyze_resume()` connect `Analysis Orchestration` to `Text Extraction Layer`, `Job Description Matching`, `Keyword & Formatting Checks`, `Statistics & Benchmarks`, `Contact Info Detection`, `ATS Compatibility Checks`?**
  _High betweenness centrality (0.373) - this node is a cross-community bridge._
- **Why does `analyze_resume` connect `Resume Scoring Engine` to `Text Extraction Layer`, `Analysis Orchestration`?**
  _High betweenness centrality (0.192) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `analyze_resume()` (e.g. with `home()` and `.test_empty_text()`) actually correct?**
  _`analyze_resume()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `add_user()` (e.g. with `register()` and `.test_add_user()`) actually correct?**
  _`add_user()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `home()` (e.g. with `allowed_file()` and `extract_text_from_file()`) actually correct?**
  _`home()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SQLite database setup and helper functions for the resume analyzer app.`, `Return the path to the SQLite database file.`, `Create the database and tables if they do not exist.` to the rest of the system?**
  _63 weakly-connected nodes found - possible documentation gaps or missing edges._