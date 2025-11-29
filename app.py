import os
import re
import json
from typing import Dict, List
import streamlit as st
import requests
import fitz  # PyMuPDF
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Optional: load .env into environment (install python-dotenv)
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # python-dotenv is optional; the app still works if not installed and env vars/st.secrets are used
    pass

# -----------------------
# Defaults & config
# -----------------------
API_URL_DEFAULT = "https://openrouter.ai/api/v1/chat/completions"
MODEL_DEFAULT = "openai/gpt-3.5-turbo-0613"

# -----------------------
# Utility: HTTP session with retries
# -----------------------
def create_requests_session(retries: int = 3, backoff_factor: float = 0.3) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# -----------------------
# API key resolution
# -----------------------
def get_api_key_from_secrets_or_env() -> str:
    """
    Prefer Streamlit secrets (st.secrets['OPENROUTER_API_KEY']), then environment var.
    load_dotenv() already attempted at import time to populate env from .env
    """
    try:
        if isinstance(st.secrets, dict) and st.secrets.get("OPENROUTER_API_KEY"):
            return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        # st.secrets may not be dict-like in all environments; ignore and fallback
        pass
    return os.environ.get("OPENROUTER_API_KEY", "") or os.environ.get("OPENROUTER_KEY", "")

# -----------------------
# PDF extraction & structuring
# -----------------------
@st.cache_data(show_spinner=False)
def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using PyMuPDF (fitz)."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = [page.get_text("text") for page in doc]
        return "\n".join(pages).strip()
    except Exception:
        return ""


def structure_pdf_content(raw_text: str) -> Dict[str, str]:
    """
    Heuristically split a raw text into sections using uppercase headings and common keywords.
    Returns a dict: {heading: content}.
    """
    sections: Dict[str, List[str]] = {"Introduction": []}
    current = "Introduction"
    heading_pattern = re.compile(
        r"^(?:CHAPTER|SECTION|PART|INTRODUCTION|CONCLUSION|SUMMARY|APPENDIX)\b",
        re.IGNORECASE,
    )
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.isupper() or heading_pattern.match(line):
            current = line
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {sec: " ".join(txt) for sec, txt in sections.items()}


# -----------------------
# Chunking helpers
# -----------------------
def chunk_text(text: str, max_chars: int = 3500) -> List[str]:
    """Naive character-based chunker that prefers splitting on newlines or spaces."""
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = start + max_chars
        if end >= L:
            chunks.append(text[start:L].strip())
            break
        split_at = text.rfind("\n", start, end)
        if split_at <= start:
            split_at = text.rfind(" ", start, end)
        if split_at <= start:
            split_at = end
        chunks.append(text[start:split_at].strip())
        start = split_at
    return chunks


# -----------------------
# OpenRouter API wrapper
# -----------------------
def call_openrouter(
    messages: List[dict],
    api_key: str,
    model: str = MODEL_DEFAULT,
    api_url: str = API_URL_DEFAULT,
    timeout: int = 20,
) -> dict:
    """POST to the OpenRouter-compatible chat completions endpoint and return parsed JSON."""
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set. Provide the key via st.secrets or environment variable.")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages}
    session = create_requests_session()
    resp = session.post(api_url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def safe_json_get_choice_content(resp_json: dict) -> str:
    """Safely extract assistant content from an OpenRouter-like response."""
    choices = resp_json.get("choices")
    if not choices or len(choices) == 0:
        raise RuntimeError(f"No choices returned by model. Response: {json.dumps(resp_json)[:1000]}")
    first = choices[0]
    if "message" in first and isinstance(first["message"], dict):
        content = first["message"].get("content")
    else:
        # fallback shapes
        content = first.get("text") or first.get("content")
    if content is None:
        raise RuntimeError(f"Choice content missing. Raw choice: {json.dumps(first)[:1000]}")
    return content


# -----------------------
# High-level operations: summarize, query, follow-ups
# -----------------------
def summarize_chunks(chunks: List[str], api_key: str, model: str) -> List[str]:
    """Ask the model to create short summaries for each chunk (2-3 sentences)."""
    summaries = []
    system_msg = {
        "role": "system",
        "content": "You are a concise summarizer. Summarize the following chunk in 2-3 short sentences, focusing on facts that would help answer user questions.",
    }
    for i, chunk in enumerate(chunks, start=1):
        prompt = f"Chunk {i} of {len(chunks)}:\n\n{chunk}"
        messages = [system_msg, {"role": "user", "content": prompt}]
        resp = call_openrouter(messages, api_key=api_key, model=model)
        summaries.append(safe_json_get_choice_content(resp).strip())
    return summaries


def query_pdf_content(sections: Dict[str, str], question: str, api_key: str, model: str = MODEL_DEFAULT) -> str:
    """Query the model given structured sections. Summarize chunks if necessary."""
    content = "\n\n".join(f"{sec}:\n{body}" for sec, body in sections.items())
    if not content.strip():
        raise RuntimeError("Document content is empty after extraction/structuring.")
    chunks = chunk_text(content, max_chars=3500)
    system_msg = {
        "role": "system",
        "content": "You are a helpful assistant. Answer concisely and, where appropriate, mention the section heading you used.",
    }
    if len(chunks) == 1:
        user_prompt = f"Document content:\n\n{chunks[0]}\n\nQuestion: {question}\nAnswer concisely and cite section headings if relevant."
        messages = [system_msg, {"role": "user", "content": user_prompt}]
        resp = call_openrouter(messages, api_key=api_key, model=model)
        return safe_json_get_choice_content(resp)

    # For multi-chunk docs, summarize, then ask final question on summaries
    summaries = summarize_chunks(chunks, api_key=api_key, model=model)
    combined_summary = "\n\n".join(f"Summary {i+1}: {s}" for i, s in enumerate(summaries))
    final_prompt = f"Based on the combined summaries below, answer the question concisely and indicate which summary/section(s) support the answer.\n\n{combined_summary}\n\nQuestion: {question}"
    resp = call_openrouter([system_msg, {"role": "user", "content": final_prompt}], api_key=api_key, model=model)
    return safe_json_get_choice_content(resp)


def generate_followup_questions(answer_text: str, api_key: str, model: str = MODEL_DEFAULT) -> List[str]:
    """Ask the model to produce 3 short follow-up questions (one per line)."""
    system_msg = {"role": "system", "content": "You are a concise question generator."}
    prompt = f"Based on the following answer, generate 3 brief, clear follow-up questions (one per line, no numbering):\n\n{answer_text}"
    resp = call_openrouter([system_msg, {"role": "user", "content": prompt}], api_key=api_key, model=model)
    text = safe_json_get_choice_content(resp)
    raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    cleaned = [re.sub(r"^\s*\d+[\).\s-]*", "", q) for q in raw_lines]
    return cleaned if cleaned else ["❌ No follow-up questions available."]


# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="PDF Q&A", layout="wide")
st.title("📄 PDF Q&A")

# Sidebar: API key & settings
st.sidebar.header("Settings & API")
api_key = get_api_key_from_secrets_or_env()
if not api_key:
    st.sidebar.warning("No OPENROUTER_API_KEY found in st.secrets or environment. Add it to .env or Streamlit secrets.")
api_key_input = st.sidebar.text_input("Temporary API key (paste to override)", type="password")
if api_key_input:
    api_key = api_key_input.strip()

model_name = st.sidebar.text_input("Model name", value=MODEL_DEFAULT)
api_url = st.sidebar.text_input("API URL", value=API_URL_DEFAULT)

st.sidebar.markdown(
    """
**How to set the API key**
- Local: add `OPENROUTER_API_KEY=sk-...` to a `.env` file in the repo root (do not commit).
- Streamlit Cloud: set in App Secrets.
- CI/CD: set as repository secret (GitHub Actions).
"""
)

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    with st.spinner("Extracting text from PDF..."):
        raw_text = extract_text_from_pdf_bytes(file_bytes)
    if not raw_text:
        st.error("Failed to extract text from PDF. The file may be scanned (image-only) or corrupted.")
    else:
        sections = structure_pdf_content(raw_text)
        st.success("PDF processed successfully!")
        st.subheader("Document preview")
        preview = raw_text[:4000].strip() + ("..." if len(raw_text) > 4000 else "")
        st.text_area("Extracted text (preview)", preview, height=200)
        st.write("Detected section headings:", list(sections.keys())[:30])

        question = st.text_input("Ask a question about the document:")
        if question:
            if not api_key:
                st.error("No API key available. Set OPENROUTER_API_KEY in .env, Streamlit secrets, or paste a temporary key in sidebar.")
            else:
                with st.spinner("Querying model..."):
                    try:
                        answer = query_pdf_content(sections, question, api_key=api_key, model=model_name)
                        st.subheader("Answer")
                        st.write(answer)
                        with st.expander("Follow-up Questions"):
                            try:
                                followups = generate_followup_questions(answer, api_key=api_key, model=model_name)
                                for idx, fq in enumerate(followups, start=1):
                                    st.write(f"{idx}. {fq}")
                            except Exception as e:
                                st.write("Could not generate follow-up questions:", e)
                    except Exception as e:
                        st.error(f"Failed to get answer: {e}")
else:
    st.info("Please upload a PDF to get started. Use the sidebar to provide your OPENROUTER_API_KEY if needed.")
