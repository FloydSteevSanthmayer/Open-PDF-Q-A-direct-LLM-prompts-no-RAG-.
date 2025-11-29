# openrouter-rag-pdf

An OpenRouter-compatible Retrieval-Augmented PDF Question-and-Answer (RAG) system.  
This repository demonstrates how to ingest PDF documents, extract text, generate chunk-level embeddings, perform vector retrieval with FAISS, and construct prompts for OpenRouter-style LLM responses with provenance.

Important: This project is independently developed and is not affiliated with, endorsed by, or sponsored by OpenRouter. The name is used strictly to indicate API compatibility.

## What This Project Provides

- Streamlit user interface for uploading PDFs and asking questions  
- Text extraction using PyMuPDF (per-page extraction)  
- Chunking with overlap and provenance metadata (page number, offsets)  
- Local embeddings using SentenceTransformers  
- FAISS IndexFlatIP for cosine-style similarity search  
- Prompt construction designed for OpenRouter-compatible chat models  
- Provenance-aware LLM responses  
- Dockerfile, CI workflow, Dependabot configuration  
- Mermaid diagram sources and placeholder rendered diagrams  
- Test scaffolding and contribution guidelines  

## Quick Start

### Requirements
- Python 3.10 or higher (3.11 recommended)  
- pip  
- An OpenRouter API key (OPENROUTER_API_KEY)

### Local Setup

```
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY

streamlit run app.py
```

Access the application at:  
http://localhost:8501

## Configuration / Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENROUTER_API_KEY | OpenRouter API key (required) | None |
| OPENROUTER_URL | Chat completions endpoint | https://openrouter.ai/api/v1/chat/completions |
| OPENROUTER_MODEL | Model name used for LLM queries | openai/gpt-3.5-turbo-0613 |
| EMBED_MODEL_NAME | Local embedding model | all-MiniLM-L6-v2 |

Use `.env` for local development and `st.secrets` for Streamlit Cloud.  
Do not commit your `.env` file.

## Running with Docker

```
docker build -t openrouter-rag-pdf .
docker run --env-file .env -p 8501:8501 openrouter-rag-pdf
```

The application will be available at port 8501.

## System Overview (High-Level)

1. Upload PDF into Streamlit.  
2. Extract raw text using PyMuPDF.  
3. Split text into overlapping chunks with provenance metadata.  
4. Compute embeddings using SentenceTransformers.  
5. Index embeddings using FAISS for similarity search.  
6. Embed the user query and retrieve top-k matching chunks.  
7. Construct a structured, provenance-aware prompt.  
8. Call an OpenRouter-compatible chat completion endpoint.  
9. Display answer and retrieved source text.  

## File Overview

```
app.py                       Main Streamlit application
src/pdfqa/...                Implementation modules
flowchart_colored.mmd        Mermaid diagram source (flowchart)
architecture.mmd             System architecture diagram source
docs/
    flowchart_colored.png    Rendered diagram (placeholder)
Dockerfile
requirements.txt
.env.example
.gitignore
.github/
    workflows/ci.yml         Continuous Integration workflow
    dependabot.yml           Automated dependency updates
tests/                        pytest scaffolding
LICENSE
CONTRIBUTING.md
```

## Troubleshooting

### Syntax errors involving quotes  
Check for invalid escape sequences inside f-strings. Replace problematic strings such as `f\"...\"` with valid forms.

### No text extracted  
PDF may contain only images. Add OCR preprocessing if required.

### FAISS dimension mismatch  
Ensure all embeddings share identical dimensionality, are float32, and are normalized before insertion.

### OpenRouter API errors  
Verify:
- OPENROUTER_API_KEY is set  
- Endpoint URL is correct  
- Model name is valid  

## Contributing and CI

- Use feature branches and open pull requests.  
- Continuous Integration via GitHub Actions installs dependencies and runs tests.  
- Pre-commit hooks check formatting and common errors.

## License

Distributed under the MIT License.  
See the LICENSE file for complete terms.

## Disclaimer

This repository is independently developed and is not affiliated with OpenRouter. It is intended solely as a compatibility demonstration for educational and development use.
