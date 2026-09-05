import json
import os
import re
import streamlit as st
from docx import Document
from google import genai
from google.genai import types
from pypdf import PdfReader

# ---------------------------------------------------------
# Page Configuration & Clean Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Resume ATS Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background-color: #f8fafc; }
    .stMetric {
        background: #ffffff;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    .score-badge {
        display: inline-block;
        font-size: 2.1rem;
        font-weight: 700;
        padding: 8px 24px;
        border-radius: 9999px;
        margin-bottom: 12px;
    }
    .score-high { background-color: #dcfce7; color: #166534; }
    .score-mid { background-color: #fef9c3; color: #854d0e; }
    .score-low { background-color: #fee2e2; color: #991b1b; }
    .skill-chip {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        margin: 3px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .skill-matched { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .skill-missing { background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    </style>
    """,
    unsafe_allow_html=True,
)


def extract_text_from_file(uploaded_file) -> str:
    """Extracts raw text content from uploaded PDF or DOCX file."""
    file_type = uploaded_file.name.split(".")[-1].lower()
    text = ""

    if file_type == "pdf":
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    elif file_type in ["docx", "doc"]:
        doc = Document(uploaded_file)
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"

    return text.strip()


def analyze_resume_with_gemini(
    resume_text: str, job_description: str, api_key: str
) -> dict:
    """Evaluates ATS alignment and separates hard vs. soft skills."""
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert ATS (Applicant Tracking System) reviewer and corporate technical recruiter.
    Evaluate the candidate resume strictly against the target job description.

    Resume:
    \"\"\"{resume_text}\"\"\"

    Job Description:
    \"\"\"{job_description}\"\"\"

    Return ONLY a single valid JSON object strictly matching this schema:
    {{
      "ats_score": <int between 0 and 100>,
      "match_summary": "<2-3 sentence overview of profile alignment>",
      "hard_skills": {{
        "matched": ["matched technical/hard skill 1", "tool 2"],
        "missing": ["missing technical/hard skill 1", "framework 2"]
      }},
      "soft_skills": {{
        "matched": ["matched soft skill/competency 1", "competency 2"],
        "missing": ["missing soft skill/competency 1", "competency 2"]
      }},
      "strengths": ["Clear strength 1", "Clear strength 2"],
      "improvements": ["Actionable improvement 1", "Improvement 2"],
      "reformatted_bullet_examples": [
        {{
          "original": "Weak original resume sentence/bullet",
          "optimized": "High-impact, metric-driven ATS alternative with action verbs"
        }}
      ]
    }}
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )

    clean_json = re.sub(
        r"^```json\s*|\s*```$", "", response.text.strip(), flags=re.MULTILINE
    )
    return json.loads(clean_json)


def get_api_key() -> str:
    """Fetches Gemini API key from Streamlit secrets or environment variables."""
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.getenv("GEMINI_API_KEY", "")


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.header("📌 About")
    st.markdown(
        """
        **ATS Resume Matcher**
        
        Compare your resume directly against target job postings using Google Gemini Flash.
        
        **How it works:**
        1. 📄 Upload your resume (`.pdf` or `.docx`).
        2. 📝 Paste the target job description.
        3. 🚀 Click **Run ATS Analysis**.
        """
    )
    st.markdown("---")
    st.caption("🔒 Analysis is private and processed securely.")

# ---------------------------------------------------------
# Main UI
# ---------------------------------------------------------
st.title("📄 AI Resume Analyzer")
st.caption(
    "Benchmark your resume against job specifications with categorized hard & soft skill tracking."
)

api_key = get_api_key()

col_left, col_right = st.columns(2, gap="medium")

with col_left:
    st.subheader("1. Candidate Resume")
    uploaded_resume = st.file_uploader(
        "Upload PDF or Word Document",
        type=["pdf", "docx"],
        help="Ensure text is selectable and not a scanned image.",
    )

with col_right:
    st.subheader("2. Target Job Description")
    job_description_input = st.text_area(
        "Paste Job Requirements & Responsibilities",
        height=210,
        placeholder="Paste full job posting or requirements here...",
    )

if st.button("Run ATS Analysis", type="primary", use_container_width=True):
    if not api_key:
        st.error(
            "API key not found. Please configure `GEMINI_API_KEY` in Streamlit secrets (Settings > Secrets) or environment variables."
        )
    elif not uploaded_resume:
        st.warning("Please upload a resume file.")
    elif not job_description_input.strip():
        st.warning("Please provide the job description.")
    else:
        with st.spinner("Analyzing resume against job specifications..."):
            try:
                resume_text = extract_text_from_file(uploaded_resume)
                if len(resume_text) < 40:
                    st.error(
                        "Extracted text is too short. Please ensure the document contains selectable text."
                    )
                else:
                    results = analyze_resume_with_gemini(
                        resume_text=resume_text,
                        job_description=job_description_input,
                        api_key=api_key,
                    )

                    st.markdown("---")
                    st.subheader("📊 Analysis Results")

                    # Score Overview
                    score = int(results.get("ats_score", 0))
                    badge_class = (
                        "score-high"
                        if score >= 75
                        else "score-mid" if score >= 50 else "score-low"
                    )

                    sc_col, sm_col = st.columns([1, 2], gap="medium")
                    with sc_col:
                        st.markdown(
                            f'<div class="score-badge {badge_class}">ATS Score: {score}/100</div>',
                            unsafe_allow_html=True,
                        )
                        st.progress(score / 100)
                    with sm_col:
                        st.markdown(
                            f"**Match Overview:** {results.get('match_summary', '')}"
                        )

                    st.markdown("---")

                    # Hard Skills vs Soft Skills Breakdown
                    st.markdown("### 🔍 Skills Parity Breakdown")
                    tab_hard, tab_soft = st.tabs(
                        [
                            "💻 Technical & Hard Skills",
                            "🤝 Soft Skills & Core Competencies",
                        ]
                    )

                    with tab_hard:
                        hard_data = results.get("hard_skills", {})
                        col_h1, col_h2 = st.columns(2, gap="medium")
                        with col_h1:
                            st.markdown("#### ✅ Matched Hard Skills")
                            h_matched = hard_data.get("matched", [])
                            if h_matched:
                                html_chips = "".join(
                                    [
                                        f'<span class="skill-chip skill-matched">{k}</span>'
                                        for k in h_matched
                                    ]
                                )
                                st.markdown(
                                    html_chips, unsafe_allow_html=True
                                )
                            else:
                                st.caption(
                                    "No matching technical skills identified."
                                )
                        with col_h2:
                            st.markdown("#### ⚠️ Missing Hard Skills")
                            h_missing = hard_data.get("missing", [])
                            if h_missing:
                                html_chips = "".join(
                                    [
                                        f'<span class="skill-chip skill-missing">{k}</span>'
                                        for k in h_missing
                                    ]
                                )
                                st.markdown(
                                    html_chips, unsafe_allow_html=True
                                )
                            else:
                                st.caption("No critical hard skills missing.")

                    with tab_soft:
                        soft_data = results.get("soft_skills", {})
                        col_s1, col_s2 = st.columns(2, gap="medium")
                        with col_s1:
                            st.markdown("#### ✅ Matched Soft Skills")
                            s_matched = soft_data.get("matched", [])
                            if s_matched:
                                html_chips = "".join(
                                    [
                                        f'<span class="skill-chip skill-matched">{k}</span>'
                                        for k in s_matched
                                    ]
                                )
                                st.markdown(
                                    html_chips, unsafe_allow_html=True
                                )
                            else:
                                st.caption("No matching soft skills identified.")
                        with col_s2:
                            st.markdown("#### ⚠️ Missing Soft Skills")
                            s_missing = soft_data.get("missing", [])
                            if s_missing:
                                html_chips = "".join(
                                    [
                                        f'<span class="skill-chip skill-missing">{k}</span>'
                                        for k in s_missing
                                    ]
                                )
                                st.markdown(
                                    html_chips, unsafe_allow_html=True
                                )
                            else:
                                st.caption("No critical soft skills missing.")

                    st.markdown("---")

                    # Strengths and Improvements
                    c1, c2 = st.columns(2, gap="medium")
                    with c1:
                        st.markdown("### 🌟 Profile Strengths")
                        for s in results.get("strengths", []):
                            st.markdown(f"- {s}")
                    with c2:
                        st.markdown("### 🛠️ Actionable Improvements")
                        for imp in results.get("improvements", []):
                            st.markdown(f"- {imp}")

                    # Optimized Bullets
                    rewrites = results.get("reformatted_bullet_examples", [])
                    if rewrites:
                        st.markdown("---")
                        st.markdown("### ✍️ Impact-Driven Bullet Rewrites")
                        for idx, item in enumerate(rewrites, 1):
                            with st.expander(
                                f"Optimization {idx}", expanded=True
                            ):
                                st.markdown(
                                    f"**Original:** {item.get('original', '')}"
                                )
                                st.markdown(
                                    f"**ATS-Optimized:** {item.get('optimized', '')}"
                                )

            except Exception as e:
                st.error(f"Error occurred during analysis: {e}")
