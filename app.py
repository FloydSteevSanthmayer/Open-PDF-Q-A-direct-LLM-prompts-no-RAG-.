import os, re, json
from typing import Dict, List
import streamlit as st
from src.pdfqa.utils import extract_text_from_pdf_bytes, structure_pdf_content, query_pdf_content, generate_followup_questions

st.set_page_config(page_title="PDF Q&A", layout="wide")
st.title("📄 PDF Q&A")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
if uploaded_file is not None:
    raw_text = extract_text_from_pdf_bytes(uploaded_file.read())
    if not raw_text:
        st.error("Failed to extract text from PDF.")
    else:
        sections = structure_pdf_content(raw_text)
        st.success("PDF processed successfully!")
        st.write("Detected sections:", list(sections.keys())[:20])

        question = st.text_input("Ask a question about the document:")
        if question:
            with st.spinner("Getting answer..."):
                try:
                    answer = query_pdf_content(sections, question)
                    st.subheader("Answer")
                    st.write(answer)

                    with st.expander("Follow-up Questions"):
                        followups = generate_followup_questions(answer)
                        for idx, fq in enumerate(followups, start=1):
                            st.write(f"{idx}. {fq}")
                except Exception as e:
                    st.error(f"Failed to get answer: {e}")
else:
    st.info("Please upload a PDF to get started.")
