# Resume I.Q.

Resume I.Q. is an AI-powered tool that analyzes the gap between a resume and a target job description, then surfaces concrete, actionable feedback on what's missing, what's weak, and what's already a strong match.

Instead of guessing whether your resume is "ATS-friendly" or "tailored enough," Resume I.Q. uses an LLM to break down both documents, compare them section by section, and generate a structured gap analysis: missing skills, keyword mismatches, experience gaps, and suggested rewrites.

## Features

- **Resume & job description parsing** — ingests PDF/DOCX resumes and raw job postings, normalizes them into clean, structured text
- **LLM-powered gap analysis** — identifies missing skills, keyword mismatches, and experience gaps between a resume and a target role
- **Structured, actionable output** — results are organized (not a wall of text) so you know exactly what to fix
- **Retrieval-ready architecture** — built with a retrieval layer and vector store from day one, so it's straightforward to extend into full RAG (e.g. pulling in your past projects, certifications, or a library of strong resume phrasing) as the project grows

## How It Works

1. **Ingest** — the resume and job description are parsed from PDF/DOCX/raw text and normalized into clean, structured text.
2. **Chunk & embed** *(optional, for retrieval-augmented runs)* — text is split into chunks and embedded for similarity search.
3. **Retrieve** *(optional)* — relevant context (past projects, certifications, phrasing examples) is pulled in via the vector store.
4. **Analyze** — the resume and job description are compared section by section using an LLM prompt tuned for gap analysis.
5. **Report** — the result is returned as structured output: missing skills, keyword mismatches, experience gaps, and suggested rewrites.

## Project Structure

```
resume-iq/
├── config/          # Runtime configuration (model names, chunk sizes, thresholds)
├── data/            # raw/, processed/, and vector_store/ artifacts
├── ingestion/       # Parses & cleans resumes and job descriptions
├── embeddings/      # Text -> vector embedding logic
├── retrieval/       # Vector store client & retrieval logic
├── prompts/         # LLM prompt templates and builders
├── analysis/        # Orchestration layer — runs the full pipeline
├── tests/           # One test file per module
└── main.py          # CLI entry point
```

See [`structure.md`](structure.md) for a detailed breakdown of each folder, its responsibilities, and conventions for where new code belongs.

## Getting Started

### Prerequisites

- Python 3.10+
- An API key for your LLM provider (e.g. OpenAI)

### Installation

```bash
git clone https://github.com/yourusername/resume-iq.git
cd resume-iq
pip install -r requirements.txt
cp .env.example .env  # add your API keys
```

### Usage

```bash
python main.py --resume path/to/resume.pdf --jd path/to/job_description.txt
```

This runs the resume through the full pipeline (parse → analyze) against the given job description and prints a structured gap analysis: missing skills, keyword mismatches, experience gaps, and suggested rewrites.

## Roadmap

- [x] Core LLM-based gap analysis (resume vs. single job description)
- [ ] Vector database integration for retrieval-augmented suggestions
- [ ] Support for batch analysis (one resume vs. multiple job descriptions)
- [ ] Web UI / API layer

## Contributing

Contributions are welcome. Before adding code, check [`structure.md`](structure.md) for where new logic belongs (ingestion, embeddings, retrieval, prompts, or analysis) and add a corresponding test under `tests/`.

## License

This project is licensed under the [MIT License](LICENSE).
