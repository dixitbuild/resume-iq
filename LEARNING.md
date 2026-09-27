# Learning Path: AI Engineering via Resume I.Q.

Context: backend engineer, production experience with Python/Django. Skipping
tutorials — learning AI engineering by building this project feature by
feature. This file is the curriculum: each phase names the concepts to learn
*before* writing that phase's code, and the concrete thing to build that
forces you to actually use them. Work top to bottom — each phase leans on the
one before it, same as the pipeline in [structure.md](structure.md).

How to use this: don't let me hand you finished files. Read the "Learn"
list, go understand those terms (ask me to explain any of them, or read
docs), then build the "Build" item yourself. I'll review, not write, unless
you ask me to pair on a specific stuck point. Check boxes off as you go.

---

## Phase 0 — What's different from Django

Skip if obvious, but worth stating once: in Django, correctness is
deterministic — same input, same output, and bugs are logic errors. In AI
engineering, a chunk of the system (the LLM/embedding call) is
non-deterministic and probabilistic — same input can give different output,
"correct" is fuzzy, and a lot of the job is *measuring* quality rather than
just fixing bugs. Keep that in mind going in: things like "add a test" work
differently once an LLM is in the loop (see Phase 7).

---

## Phase 1 — Ingestion: getting clean text out of a resume

- [x] **Learn**
  - [x] Why PDF/DOCX aren't "text with a different extension" — PDF stores
    positioned glyphs, not reading order; DOCX stores structured XML
  - [x] What text-extraction libraries actually do under the hood (`pypdf`,
    `python-docx`) and where they lose information (columns, tables, headers)
  - [x] Why downstream AI steps are sensitive to garbage input (whitespace noise
    burns tokens; broken sentence flow hurts embedding quality) — "garbage
    in, garbage embedding" is the AI-era version of "garbage in, garbage out"
- [ ] **Build** — `ingestion/parsers.py` (extract raw text from
  .pdf/.docx/.txt) and `ingestion/cleaners.py` (normalize whitespace, strip
  artifacts)
- [ ] **Done when** — you can feed in a real PDF resume and get back a
  clean, readable string with no stray `\x0c`/`\xa0`/double-spacing

---

## Phase 2 — Tokenization & chunking

- [ ] **Learn**
  - What a *token* actually is — BPE subword units, not words or characters
    (play with `tiktoken` directly in a REPL, encode/decode some sentences,
    look at where it splits words)
  - Why every LLM and embedding model has a token limit, and why that's a
    *hard* constraint (not a style preference)
  - Chunking strategies and their tradeoffs: fixed-size token windows (what
    you'll build first) vs. sentence/paragraph-aware vs. semantic chunking
  - Why chunk *overlap* exists (context that straddles a cut boundary)
  - Why smaller chunks ≠ better — the precision/context tradeoff (a
    one-sentence chunk retrieves precisely but has no surrounding context;
    a full-page chunk has context but dilutes the embedding's meaning)
- [ ] **Build** — `embeddings/chunking.py`: split cleaned text into
  overlapping token-bounded chunks; `config/settings.yaml` for chunk
  size/overlap so you can tune without redeploying code
- [ ] **Done when** — you can chunk a resume at different `chunk_size`
  values and *explain* why a search for one skill would retrieve differently
  at each size (even before you've built retrieval)

---

## Phase 3 — Embeddings

- [ ] **Learn**
  - What an embedding actually is: a vector that places text in a
    high-dimensional space such that "similar meaning" = "close together" —
    this is the core trick that makes semantic search possible at all
  - Cosine similarity / dot product — how "closeness" is actually measured
  - Embedding model choices and what changes between them: dimensionality,
    cost per token, max input size, general-purpose vs.
    code/domain-specific models
  - Why you embed at the *chunk* level, not the whole document (ties back
    to Phase 2)
  - Cost and latency — embeddings are billed per token; batch calls when
    you can
- [ ] **Build** — `embeddings/embedder.py`: wraps a call to an embedding
  API (or a local `sentence-transformers` model if you want to avoid API
  cost while learning) and returns a vector per chunk
- [ ] **Done when** — you can embed two resume chunks that are semantically
  similar (e.g. "led backend team" vs. "managed engineering team") and two
  that aren't, and confirm via cosine similarity that the numbers reflect
  that — this is the first time you'll *see* the "meaning as geometry" idea
  work, not just read about it

---

## Phase 4 — Talking to an LLM directly (prompting fundamentals)

This is the actual "Core LLM-based gap analysis" feature — build it
*without* retrieval first (resume text + JD text, both pasted straight into
the prompt). Retrieval comes later in Phase 6 and only matters once the
context you need doesn't fit in one prompt.

- [ ] **Learn**
  - Anthropic/OpenAI SDK basics: messages API, system vs. user role, what a
    "completion" call actually sends over the wire
  - Context window vs. embedding token limit — different numbers, don't
    confuse them
  - Getting structured output back (JSON mode / tool-use / forcing a
    schema) instead of parsing free text — critical for a pipeline, not
    optional
  - Temperature and why you'd want it near 0 for an analytical task like
    this vs. higher for creative rewrites
  - Prompt structure: instructions, the actual documents, and how you
    format expected output all matter more than you'd expect coming from
    deterministic code
- [ ] **Build** — `prompts/gap_analysis.py` + `prompts/templates/` (the
  prompt text, kept separate from code per `structure.md`), plus a script
  that sends resume + JD text to the LLM and gets back structured JSON:
  missing skills, keyword mismatches, experience gaps, suggested rewrites
- [ ] **Done when** — running it against a real resume/JD pair gives you
  output you'd actually trust enough to act on, and you understand *why*
  the prompt is shaped the way it is (not just that it works)

---

## Phase 5 — Orchestration

- [ ] **Learn**
  - Why the "orchestration layer" pattern exists — one place that calls
    ingestion → embeddings → prompts, so no other module reaches across
    boundaries (this is standard in AI pipelines because so many pieces are
    external API calls with their own failure modes)
  - Handling LLM API failures: rate limits, timeouts, retries with backoff
    — different from typical Django DB error handling because these calls
    are slow, non-deterministic, and cost money per attempt
  - Validating LLM output against a schema (e.g. Pydantic) before trusting
    it downstream — the LLM *will* eventually return malformed JSON
- [ ] **Build** — `analysis/gap_engine.py`: runs parse → prompt → validate
  → structure output; wire it into `main.py` as the real CLI entry point
- [ ] **Done when** — `python main.py --resume x.pdf --jd y.txt` reliably
  produces a structured report, and a malformed LLM response doesn't crash
  the whole run

---

## Phase 6 — Vector store & retrieval (this is where it becomes RAG)

- [ ] **Learn**
  - What a vector database actually adds over "loop through a list of
    vectors and compute cosine similarity" (indexing structures like HNSW —
    know it exists, don't need to implement it)
  - Concrete options and when each makes sense: FAISS (local, no server),
    Chroma (local, a bit more batteries-included), pgvector (if you already
    have Postgres — you're coming from Django, this one will feel familiar)
  - Top-k retrieval, similarity thresholds, and *relevance filtering* — top
    result isn't automatically "relevant enough to use"
  - The actual RAG pattern end to end: embed a query → search → stuff
    top-k chunks into a prompt → generate — and *why* this beats just
    pasting everything into context (cost, the model attending better to
    less irrelevant text, handling corpora too big for any context window)
  - When RAG is the wrong tool (small, fixed documents that fit in context
    — like this project's current resume-vs-JD case — often don't need it)
- [ ] **Build** — `retrieval/vector_store.py` (upsert/query/delete against
  your chosen store) and `retrieval/retriever.py` (top-k + filtering on top
  of it); extend `gap_engine.py` to optionally pull in a small corpus (past
  projects, certifications, a library of strong resume phrasing) as extra
  context for the LLM
- [ ] **Done when** — you can add a new document to the corpus, ask a
  question, and see retrieval actually surface the relevant chunk instead
  of an unrelated one — and you can explain a case where it *fails* to
  retrieve the right thing and why

---

## Phase 7 — Evaluation (the part tutorials almost always skip)

- [ ] **Learn**
  - Why "it looked right when I tried it" isn't good enough once an LLM is
    in the loop — you need a repeatable way to catch regressions when you
    change a prompt or swap a model
  - Building a small golden dataset: a handful of resume/JD pairs with
    expected gap-analysis output you've manually checked
  - LLM-as-judge pattern — using a second LLM call to score output quality
    against a rubric, and its own failure modes (judge bias, cost)
  - Retrieval-specific metrics: precision/recall@k for whether the right
    chunks came back at all, separate from whether the final LLM answer
    was good
- [ ] **Build** — `tests/` gets an eval harness, not just unit tests: a
  small fixed dataset + a script that runs the pipeline against it and
  reports pass/fail or a quality score
- [ ] **Done when** — you can change a prompt, rerun the eval set, and get
  a number telling you if you made things better or worse — instead of
  guessing

---

## Phase 8 — Batch processing

- [ ] **Learn**
  - Concurrent/async LLM calls (`asyncio` + async SDK clients) and why
    naive parallel loops hit rate limits fast
  - Cost tracking across many calls — you'll want to know what a batch run
    costs *before* running it against 50 resumes
- [ ] **Build** — batch mode: one resume against multiple job descriptions,
  or multiple resumes against one JD, run concurrently with a rate limiter
- [ ] **Done when** — a batch of N comparisons finishes faster than N
  sequential calls, without tripping rate limits, and you can report total
  cost

---

## Phase 9 — Serving it (Web UI / API layer)

- [ ] **Learn**
  - Serving long-running LLM calls without blocking — streaming responses,
    async request handlers (FastAPI, since Django's sync-first model fights
    this pattern more than it helps here)
  - Where to cache: embeddings and chunks rarely change for a given
    document, so re-embedding on every request is wasted cost
- [ ] **Build** — a thin API layer over `analysis/gap_engine.py` — this
  should be a small wrapper, since all the real logic already lives in
  `analysis/`
- [ ] **Done when** — you can hit an endpoint with a resume + JD and get a
  streamed or polled result back

---

## Phase 10 — Stretch: production concerns

Not in the current roadmap, but worth knowing exist once the core pipeline
works:

- [ ] **Learn**
  - Observability for LLM apps: logging prompts, responses, token counts,
    and cost per request (you can't `print()`-debug your way through a
    probabilistic system the way you can deterministic code)
  - PII handling — resumes are personal data (names, emails, phone
    numbers); know what your pipeline sends to third-party APIs and whether
    that's acceptable
  - Guardrails / input validation against prompt injection if you ever
    accept free-text job descriptions from untrusted users
  - Basic agent patterns (tool use, multi-step reasoning) — only relevant
    if/when this project needs the LLM to take actions, not just analyze

---

## Where things stand

Nothing is built yet — the repo currently has only docs
([README.md](README.md), [structure.md](structure.md)). Start at Phase 1.
