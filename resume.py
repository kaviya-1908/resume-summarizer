"""
Streamlit Resume Summarizer (No API Keys, Streamlit Cloud Compatible)
----------------------------------------------------------------------
- Upload resumes (.pdf, .docx, .txt)
- Extracts text only (no OCR)
- Summarizes using a lightweight frequency-based algorithm
- Works fully offline — no API calls
"""

import streamlit as st
from io import BytesIO
import re
from collections import Counter, defaultdict

# PDF and DOCX readers
from PyPDF2 import PdfReader
import docx

# NLTK for NLP
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# -----------------------------
# NLTK setup (for Streamlit Cloud)
# -----------------------------
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
STOPWORDS = set(stopwords.words('english'))

# -----------------------------
# Text extractors
# -----------------------------
def extract_text_from_pdf(file_stream):
    try:
        reader = PdfReader(file_stream)
        texts = []
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                texts.append(txt)
        return "\n".join(texts)
    except Exception:
        return ""


def extract_text_from_docx(file_stream):
    try:
        document = docx.Document(file_stream)
        texts = [p.text for p in document.paragraphs if p.text.strip()]
        return "\n".join(texts)
    except Exception:
        return ""


def extract_text_from_txt(file_stream):
    try:
        raw = file_stream.read()
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="ignore")
        return str(raw)
    except Exception:
        return ""


def clean_text(text):
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -----------------------------
# Simple frequency-based summarizer
# -----------------------------
def summarize_text(text, num_sentences=None, ratio=None):
    sentences = sent_tokenize(text)
    if len(sentences) == 0:
        return ""

    words = [w.lower() for w in word_tokenize(text) if w.isalpha() and w.lower() not in STOPWORDS]
    if not words:
        return sentences[0] if sentences else ""

    freq = Counter(words)
    max_freq = max(freq.values())
    for w in freq:
        freq[w] = freq[w] / max_freq

    sent_scores = defaultdict(float)
    for i, sent in enumerate(sentences):
        for w in word_tokenize(sent.lower()):
            if w in freq:
                sent_scores[i] += freq[w]

    if num_sentences:
        k = max(1, min(len(sentences), num_sentences))
    elif ratio:
        k = max(1, int(len(sentences) * ratio))
    else:
        k = max(1, int(len(sentences) * 0.2))

    top_sentences = sorted(sent_scores.items(), key=lambda x: x[1], reverse=True)[:k]
    selected_indices = sorted([idx for idx, _ in top_sentences])
    summary = " ".join([sentences[i] for i in selected_indices])
    return summary


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Resume Summarizer", layout="centered")
st.title("📄 Resume Summarizer (No API Keys Needed)")
st.write("Upload a `.pdf`, `.docx`, or `.txt` resume to generate a text summary.")

file = st.file_uploader("Choose a resume file", type=["pdf", "docx", "txt"])

with st.sidebar:
    st.header("⚙️ Settings")
    show_raw = st.checkbox("Show extracted text", value=False)
    mode = st.radio("Summary Mode", ["Ratio", "Fixed Sentences"])
    if mode == "Ratio":
        ratio = st.slider("Summary ratio (fraction of sentences)", 0.05, 1.0, 0.25, 0.05)
        num_sentences = None
    else:
        num_sentences = st.number_input("Number of sentences", 1, 40, 5, 1)
        ratio = None

if file:
    name = file.name.lower()
    file_bytes = BytesIO(file.read())

    if name.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        file_bytes.seek(0)
        text = extract_text_from_docx(file_bytes)
    else:
        file_bytes.seek(0)
        text = extract_text_from_txt(file_bytes)

    text = clean_text(text)

    if not text:
        st.warning("⚠️ No text could be extracted. The resume might be image-based (no OCR here).")
    else:
        if show_raw:
            with st.expander("🔍 Extracted Text"):
                st.write(text)

        summary = summarize_text(text, num_sentences=num_sentences, ratio=ratio)
        st.subheader("🧠 Summary")
        st.write(summary)

        # Download option
        st.download_button(
            "Download Summary as .txt",
            data=summary,
            file_name=f"summary_{file.name}.txt",
            mime="text/plain"
        )

else:
    st.info("⬆️ Upload a resume file to begin.")

