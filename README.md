# AI Resume & ATS Match Analyzer 📄⚡

An intelligent, clean, and intuitive web application built with **Streamlit** and **Google Gemini Flash** that benchmarks resumes against targeted job postings to generate actionable ATS (Applicant Tracking System) insights.


## Features

* **Multi-Format Parsing:** Extracts and parses selectable text directly from `.pdf` and `.docx` files.
* **ATS Compatibility Scoring:** Computes an objective alignment score out of 100 based on job criteria.
* **Keyword Gap Analysis:** Detects matched proficiencies and flags missing technical or domain-specific keywords.
* **Actionable Feedback:** Identifies core profile strengths alongside prioritized resume improvements.
* **Metric-Driven Bullet Rewrites:** Suggests quantifiable, impact-driven rewrites for weaker resume points.
* **Responsive UI:** Modern, scannable layout designed with custom Streamlit UI components.


## Tech Stack

* **Frontend / Framework:** Streamlit
* **AI Model:** Google Gemini 2.5 Flash via `google-genai` SDK
* **Document Extraction:** `pypdf`, `python-docx`
* **Language:** Python 3.10+


## Getting Started

### 1. Clone the Repository

git clone https://github.com/your-username/resume-ats-analyzer.git
cd resume-ats-analyzer

### 2. Set Up Virtual Environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Run the Application
streamlit run app.py
