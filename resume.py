import streamlit as st
import fitz  # PyMuPDF
import openai

st.set_page_config(page_title="Resume Summarizer", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("💼 AI Resume Summarizer")

uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

if uploaded_file:
    # Extract text
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()

    st.subheader("Extracted Resume Text")
    st.text_area("", text[:1000] + "...", height=200)

    if st.button("Summarize Resume"):
        prompt = f"Summarize this resume in 5 bullet points:\n\n{text[:4000]}"
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.choices[0].message.content
        st.subheader("🧠 AI Summary")
        st.write(summary)
