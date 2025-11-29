# PDF Q&A — Streamlit + OpenRouter

Professional, production-ready repository for a **PDF Question & Answer** application that
extracts text from PDFs and uses an LLM (via OpenRouter) to answer user questions.

![Flowchart](docs/flowchart_colored.png)

## Contents
- `app.py` — Streamlit launcher and user interface.
- `src/pdfqa/utils.py` — Core helpers: PDF extraction, structuring, chunking, and API wrapper.
- `docs/flowchart_colored.png` — Flowchart illustrating the end-to-end process.
- `flowchart_colored.mmd`, `architecture.mmd` — Mermaid sources for diagrams.
- CI, linting, pre-commit and tests scaffold included for professional workflows.

## Quick start (development)
1. Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` (do **not** commit keys).
2. Create a virtual environment and install requirements:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run Streamlit:
   ```bash
   streamlit run app.py
   ```

## Docker
Build and run (exposes Streamlit on 8501):
```bash
docker build -t pdf-qa-app .
docker run -e OPENROUTER_API_KEY=your_key -p 8501:8501 pdf-qa-app
```

## Tests & CI
- Tests live under `tests/` and run via `pytest`.
- A GitHub Actions CI workflow runs tests on push — see `.github/workflows/ci.yml`.

## Contributing & License
Please read `CONTRIBUTING.md` for contribution guidelines. This project is licensed under the license in `LICENSE`.

---
Generated and packaged for portability. Replace placeholders (API keys, organization name) before publishing.
