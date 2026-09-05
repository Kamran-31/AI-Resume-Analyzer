import json
import re
import streamlit as st
from docx import Document
from google import genai
from google.genai import types
from pypdf import PdfReader

# ---------------------------------------------------------
# Page Configuration & Styling
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
        font-size: 2rem;
        font-weight: 700;
        padding: 8px 22px;
        border-radius: 9999px;
        margin-bottom: 12px;
    }
    .score-high { background-color: #dcfce7; color: #166534; }
    .score-mid { background-color: #fef9c3; color: #854d0e; }
    .score-low { background-color: #fee2e2; color: #991b1b; }
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
    """Evaluates ATS alignment and returns structured analysis using Gemini Flash."""
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert ATS (Applicant Tracking System) reviewer and hiring manager.
    Evaluate the candidate's resume strictly against the target job description.

    Resume:
    """{resume_text}"""

    Job Description:
    """{job_description}"""

    Return ONLY a single valid JSON object strictly matching this schema:
    {{
      "ats_score": <int 0-100>,
      "match_summary": "<2-3 sentence overview of match strength>",
      "matched_keywords": ["keyword1", "keyword2"],
      "missing_keywords": ["keyword1", "keyword2"],
      "strengths": ["strength1", "strength2"],
      "improvements": ["improvement1", "improvement2"],
      "reformatted_bullet_examples": [
        {{
          "original": "original weak point",
          "optimized": "high-impact bullet point with action verbs and metrics"
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

    clean_json = re.sub(r"^```json\s*|\s*```$", "", response.text.strip(), flags=re.MULTILINE)
    return json.loads(clean_json)


# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        help="Obtain an API key from Google AI Studio",
    )
    st.markdown("---")
    st.markdown(
        """
        **Workflow:**
        1. Upload Resume (`.pdf` or `.docx`)
        2. Paste Target Job Description
        3. Run ATS Analysis
        """
    )

# Main UI
st.title("📄 AI Resume & ATS Match Analyzer")
st.caption("Powered by Google Gemini Flash & Streamlit")

col_left, col_right = st.columns(2, gap="medium")

with col_left:
    st.subheader("1. Candidate Resume")
    uploaded_resume = st.file_uploader(
        "Upload PDF or Word Document",
        type=["pdf", "docx"],
    )

with col_right:
    st.subheader("2. Target Job Description")
    job_description_input = st.text_area(
        "Paste Job Requirements & Responsibilities",
        height=210,
        placeholder="Paste full job description here...",
    )

if st.button("Run ATS Analysis", type="primary", use_container_width=True):
    if not api_key_input:
        st.error("Please enter your Gemini API key in the sidebar.")
    elif not uploaded_resume:
        st.warning("Please upload a resume file.")
    elif not job_description_input.strip():
        st.warning("Please provide the job description.")
    else:
        with st.spinner("Analyzing resume against job description..."):
            try:
                resume_text = extract_text_from_file(uploaded_resume)
                if len(resume_text) < 40:
                    st.error("Extracted text is too short. Please ensure the document contains readable text.")
                else:
                    results = analyze_resume_with_gemini(
                        resume_text=resume_text,
                        job_description=job_description_input,
                        api_key=api_key_input,
                    )

                    st.markdown("---")
                    st.subheader("📊 Analysis Results")

                    score = int(results.get("ats_score", 0))
                    badge_class = "score-high" if score >= 75 else "score-mid" if score >= 50 else "score-low"

                    sc_col, sm_col = st.columns([1, 2], gap="medium")
                    with sc_col:
                        st.markdown(
                            f'<div class="score-badge {badge_class}">ATS Score: {score}/100</div>',
                            unsafe_allow_html=True,
                        )
                        st.progress(score / 100)
                    with sm_col:
                        st.markdown(f"**Overview:** {results.get('match_summary', '')}")

                    st.markdown("---")

                    kw1, kw2 = st.columns(2, gap="medium")
                    with kw1:
                        st.markdown("### ✅ Matched Keywords")
                        matched = results.get("matched_keywords", [])
                        st.write(", ".join([f"`{k}`" for k in matched]) if matched else "None detected.")

                    with kw2:
                        st.markdown("### ⚠️ Missing Keywords & Skills")
                        missing = results.get("missing_keywords", [])
                        st.write(", ".join([f"`{k}`" for k in missing]) if missing else "None missing.")

                    st.markdown("---")

                    c1, c2 = st.columns(2, gap="medium")
                    with c1:
                        st.markdown("### 🌟 Profile Strengths")
                        for s in results.get("strengths", []):
                            st.markdown(f"- {s}")
                    with c2:
                        st.markdown("### 🛠️ Key Improvements Needed")
                        for imp in results.get("improvements", []):
                            st.markdown(f"- {imp}")

                    rewrites = results.get("reformatted_bullet_examples", [])
                    if rewrites:
                        st.markdown("---")
                        st.markdown("### ✍️ Optimized Bullet Examples")
                        for idx, item in enumerate(rewrites, 1):
                            with st.expander(f"Optimization {idx}", expanded=True):
                                st.markdown(f"**Original:** {item.get('original', '')}")
                                st.markdown(f"**ATS-Optimized:** {item.get('optimized', '')}")

            except Exception as e:
                st.error(f"Error occurred during analysis: {e}")
