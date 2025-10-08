import streamlit as st
import pdfplumber
import docx2txt
import re
from gensim.summarization import summarize
from transformers import pipeline

# --- Utility functions ---
def read_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def read_docx(file):
    return docx2txt.process(file)

def clean_text(s):
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def extractive_summary(text, ratio=0.1):
    try:
        return summarize(text, ratio=ratio)
    except ValueError:
        return " ".join(text.split('.')[:5])

# --- Streamlit UI ---
st.set_page_config(page_title="Resume Summarizer", page_icon="📄", layout="wide")
st.title("📄 Resume Summarizer (No API Key Needed)")

uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Reading your resume..."):
        if uploaded_file.name.endswith(".pdf"):
            text = read_pdf(uploaded_file)
        else:
            text = read_docx(uploaded_file)

    text = clean_text(text)
    st.subheader("Extracted Text Preview:")
    st.text_area("", text[:1500] + ("..." if len(text) > 1500 else ""), height=200)

    option = st.radio("Choose summarization type:", ["Extractive (Fast)", "Abstractive (AI-based)"])

    if st.button("Generate Summary"):
        if option == "Extractive (Fast)":
            summary = extractive_summary(text)
        else:
            st.info("Loading local summarization model (this might take a few seconds)...")
            summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
            summary = summarizer(text[:3000], max_length=200, min_length=50, do_sample=False)[0]['summary_text']

        st.success("✅ Summary Generated!")
        st.text_area("Resume Summary:", summary, height=250)
