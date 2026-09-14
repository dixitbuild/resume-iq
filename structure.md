# Project Structure

This document describes the folder and file layout for Resume I.Q. It's meant as a reference for contributors and for Claude Code (or any AI coding assistant) working in this repo — so new code lands in the right place and existing conventions are followed.

## Layout

```
resume-iq/
├── config/
│   └── settings.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── vector_store/
├── ingestion/
│   ├── __init__.py
│   ├── parsers.py
│   └── cleaners.py
├── embeddings/
│   ├── __init__.py
│   ├── embedder.py
│   └── chunking.py
├── retrieval/
│   ├── __init__.py
│   ├── vector_store.py
│   └── retriever.py
├── prompts/
│   ├── __init__.py
│   ├── gap_analysis.py
│   └── templates/
├── analysis/
│   ├── __init__.py
│   └── gap_engine.py
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py
│   ├── test_embeddings.py
│   ├── test_retrieval.py
│   └── test_gap_engine.py
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Folder & File Reference

### `config/`
Central place for runtime configuration — model names, chunk sizes, vector DB settings, similarity thresholds. `settings.yaml` should be the single source of truth; avoid hardcoding config values elsewhere in the codebase.

### `data/`
- `raw/` — unmodified resumes and job descriptions as originally uploaded. Never write processed output here.
- `processed/` — cleaned/parsed text, ready for embedding or prompting.
- `vector_store/` — local vector DB persistence files (e.g. Chroma/FAISS index). Treat as generated/disposable, not hand-edited.

### `ingestion/`
Turns raw files into clean text.
- `parsers.py` — extracts text from PDF/DOCX resumes and job postings.
- `cleaners.py` — normalizes whitespace, strips headers/footers, splits into sections.

New file-format support (e.g. a new resume file type) belongs here.

### `embeddings/`
Turns text into vectors.
- `embedder.py` — wraps calls to the embedding model (OpenAI, sentence-transformers, etc.). Swap providers here, not in calling code.
- `chunking.py` — splits resume/JD text into chunks sized for embedding.

### `retrieval/`
Vector search layer, built ahead of need so RAG can be added without refactoring.
- `vector_store.py` — thin client around the vector DB (upsert, query, delete).
- `retriever.py` — top-k retrieval logic and relevance filtering, on top of `vector_store.py`.

### `prompts/`
All LLM prompt content lives here, separate from orchestration logic.
- `gap_analysis.py` — builds the prompt(s) used for resume-vs-JD comparison.
- `templates/` — raw `.txt`/`.jinja` prompt files. Prefer editing templates here over embedding prompt strings directly in Python.

### `analysis/`
Orchestration layer — the only place that should call ingestion, embeddings, retrieval, and prompts together.
- `gap_engine.py` — runs the full pipeline: parse → (retrieve) → prompt LLM → structure output.

If you're adding a new end-to-end capability, it should be orchestrated from here, not from `main.py` directly.

### `tests/`
One test file per major module, named `test_<module>.py`. Add a test file here whenever a new module is added elsewhere.

### `main.py`
CLI entry point only. Parses arguments and calls into `analysis/`. Should stay thin — no business logic here.

### `requirements.txt`
Pinned Python dependencies.

### `.env.example`
Template for required environment variables (API keys, etc.). Never commit a real `.env`.

### `.gitignore`
Should exclude `.env`, `data/raw/`, `data/processed/`, `data/vector_store/`, and standard Python artifacts (`__pycache__/`, `.venv/`, etc.).

## Conventions for New Code

- New file-parsing logic → `ingestion/`
- New embedding provider or chunking strategy → `embeddings/`
- New vector DB or retrieval strategy → `retrieval/`
- New or edited prompt wording → `prompts/templates/`
- New pipeline behavior (multi-JD comparison, batch mode, etc.) → `analysis/`
- Every new module gets a corresponding `tests/test_<module>.py`

Keeping this file up to date as the structure evolves helps both human contributors and AI coding tools (like Claude Code) make consistent decisions about where code belongs.