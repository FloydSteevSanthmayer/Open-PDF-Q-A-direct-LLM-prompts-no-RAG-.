# openrouter-rag-pdf

A professional, developer-focused Retrieval-Augmented Generation (RAG) pipeline for question answering over PDF documents.  
This project demonstrates end‑to‑end ingestion, text extraction, chunking with provenance, local embedding generation, vector retrieval with FAISS, and OpenRouter‑compatible LLM prompting.

Important: This repository is independently maintained and is not affiliated with, endorsed by, or sponsored by OpenRouter. The name is used solely to indicate API compatibility.

---

## Project Overview

`openrouter-rag-pdf` provides a clean and extensible template for building RAG workflows around PDFs. It includes:

- Fast per‑page text extraction using PyMuPDF  
- Chunking with overlap and provenance metadata (page numbers and offsets)  
- Local embeddings via SentenceTransformers  
- FAISS IndexFlatIP for efficient cosine‑similarity retrieval  
- Structured prompts and OpenRouter‑compatible LLM completions  
- A minimal Streamlit interface for experimentation  
- Docker support, CI scaffolding, dependency automation, and test templates  

This repository is intended as a foundation for prototypes, demos, or small‑scale document‑QA projects.

---

## Features

- Streamlit UI for PDF upload and question answering  
- Per‑page extraction using PyMuPDF  
- Chunking with configurable overlap and embedded provenance  
- Local embeddings with SentenceTransformers  
- FAISS vector search using normalized vectors  
- Compatible with OpenRouter chat completions  
- Support for answer provenance and follow‑up question generation  
- Dockerfile and GitHub Actions workflow  
- Dependabot configuration for automated dependency updates  
- Basic pytest scaffold  

---

## Quick Start

### Requirements
- Python 3.10+ (3.11 recommended)
- pip
- An OpenRouter API key (`OPENROUTER_API_KEY`)

### Local Setup

```
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY
streamlit run app.py
```

Visit: http://localhost:8501

---

## Configuration

Supported environment variables:

| Variable             | Description                                   | Default |
|----------------------|-----------------------------------------------|---------|
| OPENROUTER_API_KEY   | Required LLM API key                           |         |
| OPENROUTER_URL       | Chat completions endpoint                     | https://openrouter.ai/api/v1/chat/completions |
| OPENROUTER_MODEL     | Model to query                                 | openai/gpt-3.5-turbo-0613 |
| EMBED_MODEL_NAME     | Local embedding model name                     | all-MiniLM-L6-v2 |

Use `.env` for local development and `st.secrets` for Streamlit Cloud.

---

## Running with Docker

```
docker build -t openrouter-rag-pdf .
docker run --env-file .env -p 8501:8501 openrouter-rag-pdf
```

---

## High‑Level Architecture

1. Upload PDF  
2. Extract per‑page text using PyMuPDF  
3. Chunk content with word‑overlap and provenance  
4. Embed chunks using SentenceTransformers  
5. Index embeddings using FAISS (IndexFlatIP)  
6. Retrieve top‑k relevant chunks for user queries  
7. Construct structured prompts containing retrieved context  
8. Send prompts to an OpenRouter‑compatible chat completion endpoint  
9. Produce answer and provenance metadata  

---

## Files of Interest

- `app.py` — main Streamlit application  
- `flowchart_colored.mmd`, `architecture.mmd` — Mermaid diagram sources  
- `docs/` — rendered diagram images  
- `Dockerfile`, `requirements.txt`, `.env.example`  
- `.github/workflows/ci.yml` — CI pipeline  
- `.github/dependabot.yml` — dependency automation  
- `tests/` — pytest scaffold  
- `LICENSE` — MIT license  
- `CONTRIBUTING.md` — contribution guidelines  

---

## Troubleshooting

### No text extracted  
The PDF may contain scanned images only. Add OCR preprocessing using Tesseract or a similar tool.

### FAISS dimension mismatch  
Ensure:
- All embeddings share the same dimension  
- Embeddings are normalized  
- Vector dtype is float32  

### LLM call fails  
Verify:
- `OPENROUTER_API_KEY` is set  
- The configured endpoint is reachable  
- Your model name is valid  

---

## Contributing

Contributions are welcome.  
Use feature branches and open pull requests.  
The repository includes a GitHub Actions workflow that installs dependencies and runs tests on every push.

---

## License

This project is released under the MIT License. See the `LICENSE` file for full details.

---

## Disclaimer

This project is independently maintained.  
It is not affiliated with, endorsed by, or sponsored by OpenRouter.
