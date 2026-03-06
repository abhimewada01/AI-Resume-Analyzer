# AI Resume Analyzer

A simple full-stack web app that lets users upload a **PDF resume**, extracts text from it, detects common **technical skills/technologies**, calculates a **resume score**, and returns **improvement suggestions**.

## Features

- **PDF resume upload**
  - Upload a `.pdf` resume (up to 10 MB)
  - Text extraction using `pdfplumber`
- **Skill extraction**
  - Uses `spaCy` (PhraseMatcher) with a curated list of skills/tech keywords
  - Displays detected skills as tags
- **Resume score**
  - Simple heuristic score (0–100) based on:
    - number of detected skills
    - presence of a Projects section
    - measurable achievements (numbers / percentages / dollar amounts)
- **Suggestions**
  - Examples:
    - add more relevant skills
    - add / improve Projects section
    - add measurable achievements
- **Clean UI + error handling**
  - Friendly errors (missing file, wrong type, extraction failures)
  - Results shown on the same page after analysis

## Project Structure

```
AI-Resume-Analyzer
│
├── app.py
├── requirements.txt
├── templates
│   └── index.html
├── static
│   └── style.css
└── README.md
```

## Installation

### 1) Create and activate a virtual environment (recommended)

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

## Run Locally

```powershell
python app.py
```

Then open:

- `http://127.0.0.1:5000`

## Screenshots (placeholders)

- Upload screen: *(add screenshot here)*
- Results screen: *(add screenshot here)*

## Notes / Limitations

- **Scanned (image) PDFs** often have no selectable text. In that case, extraction will fail and the app will prompt you to run OCR first.
- Skill extraction is based on a **keyword list** (easy to extend). Update `SKILL_KEYWORDS` in `app.py` to add more technologies.

## Future Improvements

- Add OCR support for scanned resumes (e.g., `pytesseract` + `pdf2image`)
- Add job description upload and compute a match score
- Use a richer NLP pipeline (custom skill taxonomy, embeddings, semantic matching)
- Export results as a PDF/JSON report
- User accounts + saved history

