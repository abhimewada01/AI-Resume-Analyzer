import io
import re
from dataclasses import dataclass
from typing import List, Tuple

import pdfplumber
import spacy
from flask import Flask, jsonify, render_template, request
from spacy.matcher import PhraseMatcher


app = Flask(__name__)

# Prevent huge uploads from choking the server.
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB


ALLOWED_EXTENSIONS = {"pdf"}

# A practical baseline list. You can extend this anytime.
SKILL_KEYWORDS = [
    # Languages
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "C",
    "C++",
    "C#",
    "Go",
    "Ruby",
    "PHP",
    "SQL",
    "Bash",
    # Web
    "HTML",
    "CSS",
    "React",
    "Next.js",
    "Vue",
    "Angular",
    "Node.js",
    "Express",
    "Flask",
    "Django",
    "FastAPI",
    # Data/ML
    "Pandas",
    "NumPy",
    "scikit-learn",
    "TensorFlow",
    "PyTorch",
    "spaCy",
    "NLTK",
    # Databases
    "PostgreSQL",
    "MySQL",
    "SQLite",
    "MongoDB",
    "Redis",
    # Cloud/DevOps
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",
    "CI/CD",
    "Git",
    "Linux",
    # Testing/Tools
    "pytest",
    "Jest",
    "Selenium",
]


@dataclass(frozen=True)
class AnalysisResult:
    skills: List[str]
    score: int
    suggestions: List[str]
    word_count: int


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from a PDF using pdfplumber.
    Falls back gracefully if a page has no extractable text.
    """
    text_parts: List[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def build_phrase_matcher(nlp) -> PhraseMatcher:
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in SKILL_KEYWORDS]
    matcher.add("SKILLS", patterns)
    return matcher


def extract_skills(text: str) -> List[str]:
    """
    Skill extraction via spaCy PhraseMatcher over a curated keyword list.
    This avoids needing a large language model download while still using NLP tooling.
    """
    if not text.strip():
        return []

    nlp = spacy.blank("en")
    matcher = build_phrase_matcher(nlp)

    doc = nlp(text)
    matches = matcher(doc)

    found = set()
    for _, start, end in matches:
        span_text = doc[start:end].text.strip()
        # Normalize by matching against the canonical list case-insensitively
        for canonical in SKILL_KEYWORDS:
            if canonical.lower() == span_text.lower():
                found.add(canonical)
                break
        else:
            found.add(span_text)

    return sorted(found, key=lambda s: s.lower())


def compute_resume_score(text: str, skills: List[str]) -> Tuple[int, List[str]]:
    """
    A simple scoring heuristic:
    - Skills: up to 30 points
    - Projects section: 10 points
    - Measurable achievements (numbers/percentages): 10 points
    - Baseline: 50 points
    """
    t = text.lower()

    skill_points = min(30, len(skills) * 2)  # 0..30

    has_projects = any(
        kw in t
        for kw in [
            "projects",
            "project experience",
            "personal projects",
            "academic projects",
            "capstone",
        ]
    )
    project_points = 10 if has_projects else 0

    has_metrics = bool(re.search(r"\b(\d+(\.\d+)?%?|\$\d[\d,]*)\b", text))
    metrics_points = 10 if has_metrics else 0

    score = 50 + skill_points + project_points + metrics_points
    score = max(0, min(100, score))

    suggestions: List[str] = []
    if len(skills) < 8:
        suggestions.append(
            "Add more relevant technical skills (tools, frameworks, databases) that you genuinely know."
        )
    if not has_projects:
        suggestions.append(
            "Add a Projects section with 2–4 items (problem, your role, tech stack, and outcome)."
        )
    if not has_metrics:
        suggestions.append(
            "Add measurable achievements (e.g., performance improvement %, users served, time saved, or revenue impact)."
        )
    if not suggestions:
        suggestions.append("Great baseline—consider tailoring keywords to the specific job description.")

    return score, suggestions


def analyze_resume_text(text: str) -> AnalysisResult:
    skills = extract_skills(text)
    score, suggestions = compute_resume_score(text, skills)
    words = len(re.findall(r"\b\w+\b", text))
    return AnalysisResult(skills=skills, score=score, suggestions=suggestions, word_count=words)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/analyze")
def analyze():
    if "resume" not in request.files:
        return jsonify({"error": "No file field found. Please upload a PDF resume."}), 400

    file = request.files["resume"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Please upload a PDF (.pdf)."}), 400

    try:
        pdf_bytes = file.read()
        if not pdf_bytes:
            return jsonify({"error": "Uploaded file is empty."}), 400

        text = extract_text_from_pdf_bytes(pdf_bytes)
        if not text.strip():
            return (
                jsonify(
                    {
                        "error": "Could not extract text from this PDF. If it's a scanned image, run OCR first."
                    }
                ),
                400,
            )

        result = analyze_resume_text(text)
        return jsonify(
            {
                "skills": result.skills,
                "score": result.score,
                "suggestions": result.suggestions,
                "word_count": result.word_count,
            }
        )
    except Exception:
        # Keep details off the client; return a friendly message.
        return jsonify({"error": "Analysis failed. Please try a different PDF."}), 500


if __name__ == "__main__":
    app.run(debug=True)
