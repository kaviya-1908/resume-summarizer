"""
Streamlit Resume Summarizer (No NLTK, No API keys)
--------------------------------------------------
- Upload .pdf, .docx, or .txt resumes
- Extracts text only (no OCR)
- Summarizes using simple frequency-based scoring
- Works fully offline, perfect for Streamlit Cloud
"""

import streamlit as st
from io import BytesIO
import re
from collections import Counter, defaultdict
from PyPDF2 import PdfReader
import docx

# -----------------------------
# Helper functions
# -----------------------------
def extract_text_from_pdf(file_stream):
    """Extract text from PDF"""
    try:
        reader = PdfReader(file_stream)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except Exception:
        return ""

def extract_text_from_docx(file_stream):
    """Extract text from DOCX"""
    try:
        document = docx.Document(file_stream)
        return "\n".join([p.text for p in document.paragraphs if p.text.strip()])
    except Exception:
        return ""

def extract_text_from_txt(file_stream):
    """Extract text from TXT"""
    try:
        data = file_stream.read()
        return data.decode("utf-8", errors="ignore") if isinstance(data, bytes) else str(data)
    except Exception:
        return ""

def clean_text(text):
    """Remove extra spaces and unwanted symbols"""
    text = re.sub(r"\s+", " ", text).strip()
    return text

def split_sentences(text):
    """Basic sentence splitter using regex"""
    sentences = re.split(r'(?<=[.!?]) +', text)
    return [s.strip() for s in sentences if len(s.strip()) > 3]

def tokenize_words(text):
    """Split words by non-alphabetic characters"""
    return re.findall(r"[a-zA-Z']+", text.lower())

# -----------------------------
# Simple summarizer (no nltk)
# -----------------------------
def summarize_text(text, num_sentences=None, ratio=None):
    sentences = split_sentences(text)
    if not sentences:
        return ""

    words = tokenize_words(text)
    stopwords = set([
        "the","a","an","and","is","to","in","that","for","of","on",
        "with","as","by","at","from","this","it","be","are","or",
        "was","were","can","has","have","had","but","if","not",
        "we","you","they","he","she","his","her","their","our"
    ])
    words = [w for w in words if w not in stopwords]

    if not words:
        return " ".join(sentences[:1])

    freq = Counter(words)
    max_freq = max(freq.values())
    for w in freq:
        freq[w] = freq[w] / max_freq

    sentence_scores = defaultdict(float)
    for i, sentence in enumerate(sentences):
        tokens = tokenize_words(sentence)
        for word in tokens:
            if word in freq:
                sentence_scores[i] += freq[word]

    if num_sentences:
        k = max(1, min(len(sentences), num_sentences))
    elif ratio:
        k = max(1, int(len(sentences) * ratio))
    else:
        k = max(1, int(len(sentences) * 0.25))

    ranked = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:k]
    chosen_indices = sorted([i for i, _ in ranked])
    summary = " ".join([sentences[i] for i in chosen_indices])
    return summary

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Resume Summarizer (No NLTK)", layout="centered")
st.title("📄 Resume Summarizer — No NLTK / No API Keys")

file = st.file_uploader("Upload a resume file (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

with st.sidebar:
    st.header("⚙️ Settings")
    show_text = st.checkbox("Show extracted text", value=False)
    mode = st.radio("Summary Mode", ["Ratio", "Fixed Sentences"])
    if mode == "Ratio":
        ratio = st.slider("Summary ratio (fraction of sentences)", 0.05, 1.0, 0.25, 0.05)
        num_sentences = None
    else:
        num_sentences = st.number_input("Number of sentences", 1, 40, 5, 1)
        ratio = None

if file:
    file_bytes = BytesIO(file.read())
    fname = file.name.lower()

    if fname.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif fname.endswith(".docx"):
        file_bytes.seek(0)
        text = extract_text_from_docx(file_bytes)
    else:
        file_bytes.seek(0)
        text = extract_text_from_txt(file_bytes)

    text = clean_text(text)

    if not text:
        st.warning("⚠️ No text extracted. The resume may be image-based (no OCR supported).")
    else:
        if show_text:
            with st.expander("📜 Extracted Text"):
                st.write(text)

        summary = summarize_text(text, num_sentences=num_sentences, ratio=ratio)
        st.subheader("🧠 Summary")
        st.write(summary)
        st.download_button(
            "Download Summary as .txt",
            data=summary,
            file_name=f"summary_{file.name}.txt",
            mime="text/plain"
        )
else:
    st.info("⬆️ Upload a resume to start summarizing!")

