# Flowchart — Detailed Step-by-step (for technical reviewers)

This document describes each step in the flowchart (refer to `docs/flowchart_colored.png`) with precision, implementation notes,
and considerations for reliability and security.

1. **Upload PDF**
   - User uploads a PDF via Streamlit `file_uploader`.
   - Implementation: read bytes and forward to extraction pipeline.
   - Security: Validate MIME type, enforce file size limits (e.g., 20 MB).

2. **Extract Text with PyMuPDF (fitz)**
   - Use `fitz.open(stream=file_bytes, filetype="pdf")` and `page.get_text("text")` for robust extraction.
   - Edge cases: scanned PDFs (OCR required), password-protected PDFs, extremely large files.

3. **Structure Content into Sections**
   - Heuristic: detect headings using uppercase lines and common keywords (CHAPTER, SECTION, APPENDIX).
   - Output: {section_name: content} mapping.
   - Improvement: use NLP / heading classifiers for more accurate segmentation.

4. **User Asks Question**
   - Client-side input validated (length limits).

5. **Send Prompt to OpenRouter API**
   - Chunk document or summarize when large. Use a system prompt to control output style and length.
   - Include timeout, retries and graceful fallback messages.

6. **Receive Answer**
   - Validate and sanitize model output.
   - Keep provenance: include the section name(s) or chunk references that the answer was based on.

7. **Generate Follow-up Questions**
   - Optional: ask model to create 2–3 clarifying questions to improve user interaction.

8. **Display Results**
   - Render answer and follow-ups in Streamlit UI. Provide copy and cite features (e.g., reference to section headings).

## Additional notes for reviewers
- Token management: implement token counting (tiktoken) when using large documents.
- Retrieval-augmented approach: for long documents, build embeddings (OpenAI / local) and a vector index (FAISS / Annoy).
- Security: never log API keys, use `st.secrets` or environment variables, add rate-limiting and input sanitization.
- Monitoring: track API latency, error rates, and costs. Add observability (Sentry / Prometheus).
