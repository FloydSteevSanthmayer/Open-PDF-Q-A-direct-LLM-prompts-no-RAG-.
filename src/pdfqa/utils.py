import os, re, json
from typing import Dict, List
import requests
import fitz  # PyMuPDF

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
API_URL = os.environ.get("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
MODEL_NAME = os.environ.get("OPENROUTER_MODEL", "openai/gpt-3.5-turbo-0613")

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = [page.get_text("text") for page in doc]
        return "\n".join(pages).strip()
    except Exception as e:
        return ""

def structure_pdf_content(raw_text: str) -> Dict[str, str]:
    sections: Dict[str, list] = {"Introduction": []}
    current = "Introduction"
    heading_pattern = re.compile(r"^(?:CHAPTER|SECTION|PART|INTRODUCTION|CONCLUSION|SUMMARY|APPENDIX)\\b", re.IGNORECASE)
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

def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end < len(text):
            split_at = text.rfind("\\n", start, end)
            if split_at <= start:
                split_at = text.rfind(" ", start, end)
            if split_at <= start:
                split_at = end
        else:
            split_at = len(text)
        chunks.append(text[start:split_at].strip())
        start = split_at
    return chunks

def call_openrouter(messages: List[dict], timeout: int = 15) -> dict:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"model": MODEL_NAME, "messages": messages}
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def safe_json_get_choice_content(resp_json: dict) -> str:
    choices = resp_json.get("choices")
    if not choices:
        raise RuntimeError("No choices in model response")
    message = choices[0].get("message", {})
    content = message.get("content")
    if content is None:
        raise RuntimeError("No content in model response")
    return content

def query_pdf_content(sections: Dict[str, str], question: str) -> str:
    content = "\\n\\n".join(f"{sec}:\\n{body}" for sec, body in sections.items())
    chunks = chunk_text(content, max_chars=4000)
    system_msg = {"role": "system", "content": "You are a helpful assistant. Answer concisely and cite section headings when relevant."}
    if len(chunks) == 1:
        user_prompt = f"Document content:\\n\\n{chunks[0]}\\n\\nQuestion: {question}\\nAnswer concisely."
        messages = [system_msg, {"role": "user", "content": user_prompt}]
        resp = call_openrouter(messages)
        return safe_json_get_choice_content(resp)
    summaries = []
    for i, chunk in enumerate(chunks, start=1):
        prompt = f"Chunk {i} of {len(chunks)}: Summarize this chunk in 2-3 short sentences, focusing on facts relevant to questions.\\n\\n{chunk}"
        resp = call_openrouter([system_msg, {"role": "user", "content": prompt}])
        summaries.append(safe_json_get_choice_content(resp).strip())
    combined_summary = "\\n\\n".join(f"Summary {i+1}: {s}" for i, s in enumerate(summaries))
    final_prompt = f"Based on the combined summaries below, answer the question concisely:\\n\\n{combined_summary}\\n\\nQuestion: {question}"
    resp = call_openrouter([system_msg, {"role": "user", "content": final_prompt}])
    return safe_json_get_choice_content(resp)

def generate_followup_questions(answer: str) -> List[str]:
    system_msg = {"role": "system", "content": "You are a concise question generator."}
    prompt = f"Based on the following answer, generate 3 brief follow-up questions (one per line):\\n\\n{answer}"
    resp = call_openrouter([system_msg, {"role": "user", "content": prompt}])
    text = safe_json_get_choice_content(resp)
    raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    cleaned = [re.sub(r'^\\s*\\d+[\\).\\s-]*', '', q) for q in raw_lines]
    return cleaned if cleaned else ["❌ No follow-up questions available."]
