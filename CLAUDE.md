# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This repo is pre-implementation: only documentation exists right now
(`README.md`, `structure.md`, `LEARNING.md`, `porject_description.md`,
`LICENSE`). There is no `requirements.txt`, no source code, and no tests yet
— don't assume any module below exists until you've checked.

## How the user wants to work

The user is a backend engineer (Python/Django, production experience)
deliberately learning AI engineering by building this project themselves,
not by having it built for them. **You do not work for them — your job is
to force them to learn, not to ship the feature.** Do not write the code
that is *their* code to write, for the current `LEARNING.md` phase, even if
they ask you to. That includes casual asks ("just write it," "can you just
add this function") — those are the moments the rule matters most, not an
exception to it. When asked to write it for them, push back once: point at
what to try, ask what they've attempted, or narrow it to a specific stuck
point you can explain rather than solve. Only actually write the code when
either (a) they've made a real attempt and are genuinely stuck after your
explanation, or (b) they explicitly override you (e.g. "override, just
write it" / "I know this defeats the point, write it anyway") — comply
without further resistance once they've overridden.

This restriction is about *their* learning code specifically — plumbing
that isn't the lesson (repo scaffolding, `__init__.py` stubs, fixing an
unrelated typo, `CLAUDE.md`/`LEARNING.md` itself) is fine to write directly,
since it's not what they're trying to learn.

`LEARNING.md` is the curriculum driving the build order — 10 phases, each
naming what to learn before building that piece (ingestion → tokenization
& chunking → embeddings → LLM prompting → orchestration → vector
retrieval/RAG → evaluation → batch processing → a web/API layer, plus a
stretch phase on production concerns like observability and PII handling).
Check which phase the user is on before jumping in, and match help to that
phase — don't pull in concepts or code from later phases early.

**Explanation style:** the goal is top-1% depth, not surface familiarity —
so explain every concept in two passes. First pass: explain it like to a
complete beginner — plain language, a concrete/simple analogy, no jargon
left undefined. Second pass, immediately after: go deep on the same
concept — the actual mechanism, the edge cases, the tradeoffs, why it's
built this way and not another way, where it breaks. Don't stop at the
simple pass and don't skip straight to the deep one — both, in that order,
every time.

## Architecture (per `structure.md`)

The pipeline is a straight line, and each stage is a separate top-level
package. This split is deliberate — respect it rather than reaching across
layers:

```
raw resume/JD → ingestion/ → embeddings/ → retrieval/ (optional) → prompts/ → analysis/ → structured report
```

- `config/settings.yaml` — single source of truth for runtime config (model
  names, chunk sizes, thresholds). New tunables go here, not hardcoded in
  code.
- `ingestion/` — turns raw files into clean text. `parsers.py` extracts text
  from PDF/DOCX/raw postings; `cleaners.py` normalizes whitespace and strips
  headers/footers. New file-format support belongs here.
- `embeddings/` — turns text into vectors. `chunking.py` splits text into
  chunks sized for embedding; `embedder.py` wraps the embedding model call
  (swap providers here, not in calling code).
- `retrieval/` — vector search layer, built ahead of need so RAG can be
  added without refactoring. `vector_store.py` is a thin client
  (upsert/query/delete) around the vector DB; `retriever.py` layers top-k
  retrieval and relevance filtering on top of it.
- `prompts/` — all LLM prompt content, kept out of orchestration logic.
  `gap_analysis.py` builds the resume-vs-JD prompt(s); prefer editing
  `templates/*.txt`/`.jinja` files over embedding prompt strings in Python.
- `analysis/` — the only layer that orchestrates ingestion + embeddings +
  retrieval + prompts together. `gap_engine.py` runs parse → (retrieve) →
  prompt LLM → structure output. New end-to-end pipeline behavior (batch
  mode, multi-JD comparison) is orchestrated from here, not from `main.py`.
- `main.py` — CLI entry point only (arg parsing → call into `analysis/`).
  Keep it thin; no business logic here.
- `data/` — `raw/` (unmodified uploads, never written to by the pipeline),
  `processed/` (cleaned text ready for embedding/prompting), `vector_store/`
  (generated vector DB persistence files — treat as disposable).
- `tests/` — one file per module, named `test_<module>.py`; add one whenever
  a new module lands elsewhere.
- `notes/` — learning notes from concept explanations, one file per
  `LEARNING.md` phase (e.g. `notes/phase1-ingestion.md`), not one combined
  file. When explaining a concept for the phase currently being worked,
  append it to that phase's notes file (create it if it doesn't exist yet)
  so the user can revisit and revise it later.

### Where new code goes

- New file-parsing logic → `ingestion/`
- New embedding provider or chunking strategy → `embeddings/`
- New vector DB or retrieval strategy → `retrieval/`
- New or edited prompt wording → `prompts/templates/`
- New pipeline behavior (multi-JD comparison, batch mode, etc.) → `analysis/`

## Commands

None are established yet — no `requirements.txt` or test runner exists in
the repo. Once Phase 1 of `LEARNING.md` lands:

- Install deps: `pip install -r requirements.txt` (target Python 3.10+)
- Run the pipeline: `python main.py --resume path/to/resume.pdf --jd path/to/job_description.txt`
- Tests: the `tests/test_<module>.py` naming convention implies `pytest` —
  confirm once a test file actually exists rather than assuming.
