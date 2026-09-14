# Resume I.Q.

Resume I.Q. is an AI-powered tool that analyzes the gap between a resume and a target job description, then surfaces concrete, actionable feedback on what's missing, what's weak, and what's already a strong match.

Instead of guessing whether your resume is "ATS-friendly" or "tailored enough," Resume I.Q. uses an LLM to break down both documents, compare them section by section, and generate a structured gap analysis: missing skills, keyword mismatches, experience gaps, and suggested rewrites.

## Features

- **Resume & job description parsing** — ingests PDF/DOCX resumes and raw job postings, normalizes them into clean, structured text
- **LLM-powered gap analysis** — identifies missing skills, keyword mismatches, and experience gaps between a resume and a target role
- **Structured, actionable output** — results are organized (not a wall of text) so you know exactly what to fix
- **Retrieval-ready architecture** — built with a retrieval layer and vector store from day one, so it's straightforward to extend into full RAG (e.g. pulling in your past projects, certifications, or a library of strong resume phrasing) as the project grows

## Roadmap

- [x] Core LLM-based gap analysis (resume vs. single job description)
- [ ] Vector database integration for retrieval-augmented suggestions
- [ ] Support for batch analysis (one resume vs. multiple job descriptions)
- [ ] Web UI / API layer

## Getting Started

```bash
git clone https://github.com/yourusername/resume-iq.git
cd resume-iq
pip install -r requirements.txt
cp .env.example .env  # add your API keys
python main.py --resume path/to/resume.pdf --jd path/to/job_description.txt
```

## Project Structure

See `config/`, `ingestion/`, `embeddings/`, `retrieval/`, `prompts/`, and `analysis/` for the core pipeline stages, and `tests/` for the test suite.

## License

MIT