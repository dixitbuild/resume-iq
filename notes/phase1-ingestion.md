# Phase 1 Notes — Ingestion

Notes from concept explanations during this phase's build — revisit and
revise as understanding deepens.

---

### Why PDF/DOCX aren't "text with a different extension"

A `.txt` file *is* just characters in sequence — read the bytes top to
bottom and you have the document. PDF and DOCX aren't that, for different
reasons.

**Simple version**

Think of a plain text file like a to-do list: one line after another, in
order, nothing else needed.

A PDF is closer to a printed poster. It doesn't say "here is a paragraph
of text" — it says "put the letter H at this exact x/y spot on the page,
then an e a few pixels to the right, then..." It's instructions for a
printer, optimized for *how it looks*, not *what order you should read it
in*. If the poster has two columns, nothing in the file tells you "finish
the left column before you start the right one" — that's a visual
inference humans make, not data the format stores.

A DOCX is different but still not flat text — it's a zip file full of
XML, like a flat-pack furniture kit with an instruction manual. The words
are in there, wrapped in tags describing paragraphs, styles, tables. You
have to walk the manual to pull the words out in order; you can't just
grab bytes.

**Deep version — the actual mechanism, and where it bites you**

*PDF:* the content stream is a sequence of drawing operators (`Tj`/`TJ`
to show text, `Td`/`Tm` to position it via a transformation matrix)
applied to a page's coordinate space. There is no semantic notion of
"sentence" or "paragraph" in the file — glyphs just get drawn wherever
they're positioned, in whatever order the PDF producer emitted them,
which is often the order the layout engine happened to draw things, *not*
reading order. A two-column resume can have its right-column text
interleaved with the left column in the raw stream, so a naive extractor
(`pypdf` included) walks it out cross-wise and you get sentences stitched
from unrelated sections. Fonts add another failure mode: character codes
in the stream map through a font's encoding/cmap to actual glyphs, and
non-standard encodings or ligatures can make byte-level extraction
produce mojibake unless the library resolves that mapping correctly. And
a scanned resume is just an image inside a PDF wrapper — there's no text
to extract at all without OCR.

*DOCX:* it's OOXML — unzip it and `word/document.xml` holds the body as
`<w:p>` (paragraph) → `<w:r>` (run) → `<w:t>` (text) elements. This is
genuinely structured, so `python-docx` can walk it directly rather than
guessing — but "structured" isn't the same as "matches visual reading
order." Headers/footers live in separate XML parts you have to explicitly
go fetch. Text boxes and floating shapes can live outside the main
paragraph flow entirely. Tables extract as a grid of cell elements, and a
naive extractor will often flatten that into a stream of loose words with
the row/column relationships gone.

**Why the pipeline cares:** this isn't cosmetic noise like extra
whitespace — a bad extraction can silently reorder or interleave
*content*, so a two-column resume might extract as "Senior Engineer at
Google... managed a team of 12... Bachelor's in CS..." with skills and
job history shuffled together. That's worse than the usual "garbage in,
garbage out," because downstream (chunking, embedding, the LLM prompt)
has no way to know the text is scrambled — it'll confidently analyze
nonsense as if it were a coherent resume.

This is the case for why `parsers.py` needs format-specific extraction
logic (and probably a "does this look sane" check afterward) rather than
treating `.pdf`/`.docx` as "open file, read text."

**Open question to revisit:** try pulling text out of a real PDF resume
with `pypdf` and see where the ordering actually breaks, vs. looking at
`python-docx`'s paragraph/table API.

---

### What text-extraction libraries actually do under the hood (pypdf, python-docx)

**Simple version**

`pypdf` is like someone standing in front of the "poster" (the PDF)
reading off the printer's raw instructions — "draw H here, draw e
there" — and trying to reconstruct sentences purely from where things
got drawn on the page, guessing where spaces and line breaks go based
on how far the cursor jumped between letters.

`python-docx` is more like unzipping the flat-pack box and reading the
assembly manual directly — since DOCX actually labels its parts ("this
is a paragraph," "this is a table row"), the library just walks those
labels and reads off the text tagged inside them, no guessing required.

**Deep version**

*`pypdf`:* A PDF file is a structured binary format — objects linked by
a cross-reference table, page objects pointing at a *content stream*
(often Flate/zlib-compressed). `pypdf` decompresses that stream and
tokenizes it into drawing operators: `BT`/`ET` (begin/end a text
object), `Tf` (set font+size), `Td`/`Tm` (move/set the text position),
and `Tj`/`TJ` (actually show a string). The string operand in
`Tj`/`TJ` isn't guaranteed to be readable text — it's a sequence of
*character codes* specific to that embedded font. To turn a code into
a real Unicode character, `pypdf` has to look up the font's
`ToUnicode` CMap (or an encoding `Differences` array). Some PDF
producers (especially with subsetted fonts) omit a usable `ToUnicode`
map — when that happens, extraction can't recover real characters at
all, and you get garbage or nothing.

Because there's no "paragraph" object in the file, `pypdf`
reconstructs spacing and line breaks *heuristically*: it tracks the
running text position, and when a `Td`/`TJ` jump is about the width of
a space, it inserts a space; when the y-coordinate drops by roughly a
line height, it inserts a newline. These are estimates, not facts —
which is exactly why extracted PDF text sometimes has words jammed
together or spurious line breaks mid-sentence. And it processes
operators in the order they appear in the stream, which is drawing
order, not necessarily reading order for multi-column layouts.

*`python-docx`:* DOCX is a zip archive (OPC packaging) of XML parts —
`word/document.xml` is the main body, with separate parts for
`word/header1.xml`, `word/footer1.xml`, styles, etc., wired together
by relationship (`.rels`) files. `python-docx` parses `document.xml`
with `lxml` into a real tree and exposes it as objects: a `Document`
has `.paragraphs`, each `Paragraph` has `.runs` (a *run* = `<w:r>`, a
span of text with uniform formatting), and each run's `.text` comes
straight from a `<w:t>` element. Because these tags are genuine
structure — not inferred from pixel positions — `python-docx` doesn't
need the guesswork `pypdf` does; paragraph boundaries are data, not a
heuristic.

Where it still loses things: `.paragraphs` only walks the main body,
so headers/footers (separate XML parts, referenced via section
properties) are invisible unless you explicitly go fetch those parts.
Tables (`<w:tbl>` → `<w:tr>` rows → `<w:tc>` cells, each cell
containing its own paragraphs) live outside `.paragraphs` entirely —
iterating just `.paragraphs` silently skips table content, and
reconstructing the true reading order (a paragraph, then a table, then
another paragraph) takes a different traversal. Text boxes and
floating shapes are stored under a different XML namespace
(drawingML/VML) than regular runs, so the basic `.text` properties
don't surface them at all — another silent gap, not an error.

**Where they lose information — quick reference**

*PDF (`pypdf`)*

- **Multi-column layout:** no concept of columns exists in the file;
  text is emitted in drawing order, so a naive extraction can interleave
  the left and right column line-by-line instead of reading one column
  fully before the other.
- **Tables:** no table concept at all — cell text extracts as a loose
  stream of words with row/column structure gone.
- **Headers/footers:** extracted per-page as part of the same content
  stream as the body, with no tag distinguishing them — they aren't
  cleanly separable from body text.
- **Font encoding / ligatures:** character codes in the content stream
  only become real Unicode via the font's `ToUnicode` CMap; subsetted or
  non-standard-encoded fonts can lack a usable map, producing mojibake
  or empty output instead of a clean failure.
- **Scanned pages:** if the "text" is actually a photographed or
  scanned image embedded in the PDF, there is no text layer to extract
  at all — this needs OCR, not text extraction.
- **Line breaks / spacing:** inserted heuristically from cursor-position
  jumps between glyphs, not stored as real paragraph/sentence
  boundaries — can produce merged words or spurious mid-sentence breaks.

*DOCX (`python-docx`)*

- **Tables:** genuinely modeled (`.tables`, with rows/cells), but they
  live outside `.paragraphs` — a naive walk that only reads
  `.paragraphs` skips every table silently.
- **Headers/footers:** stored in separate XML parts (`header1.xml`,
  `footer1.xml`) linked via section properties — invisible unless you
  explicitly fetch those parts; `.paragraphs` never includes them.
- **Text boxes / floating shapes:** stored under a different XML
  namespace (drawingML/VML) than normal paragraph runs, so
  `.text`/`.paragraphs` doesn't see them at all.
- **Reading order across content types:** `.paragraphs` and `.tables`
  are separate collections — reconstructing the true top-to-bottom
  order (paragraph, then table, then paragraph again) takes a different
  traversal than just concatenating each collection.

**Next step (open):** try pulling text out of a real PDF resume with
`pypdf` and see which of these actually shows up, vs. loading the same
resume as a `.docx` and inspecting `python-docx`'s paragraph/table API.

---

### Why downstream AI steps are sensitive to garbage input

**Explain-like-I'm-a-kid version**

You write a letter to your best friend. But on the way, it rains on it —
some words get smudged, and a page gets torn so two sentences get taped
together in the wrong order.

Your friend opens it and tries to read it anyway. Two bad things happen:

1. Your friend wastes time squinting at smudges that don't even say
   anything.
2. Because the sentences got mixed up, your friend might think you
   wrote something you didn't — like reading "I do not like broccoli"
   as "I like broccoli" — and they won't even know they got it wrong.
   They'll just believe it.

A computer reading a resume is just like your friend reading that
letter. It can only "read" so many words at once (like it only has so
much attention), so:

- Messy junk in the text wastes some of that attention on stuff that
  means nothing.
- If the words got jumbled (two parts of the resume stuck together
  wrong), the computer might think the resume says something it
  doesn't — and it won't raise its hand and say "hey, this looks
  weird." It'll just quietly get it wrong.

So before we let the computer read the resume, we clean it up first —
like drying off the smudges and taping the torn page back the *right*
way — so it reads the real thing, not a confused mash-up of it.

**Simplified grown-up version**

LLMs get charged and limited by "chunks of text" called tokens — every
character you feed in costs something and counts against a max. So
junk characters (stray symbols, extra blank lines) just waste money and
space for no reason.

But there's a worse problem than cost: if the text itself is scrambled
— like two sentences glued together wrong, or a word split in half —
the model doesn't error out. It just quietly misunderstands the content
and gives you a confidently wrong answer, with no warning that
anything was off.

- **Cost/limit problem:** noise (extra whitespace, weird control
  characters from PDF extraction) eats into a hard token limit and gets
  billed per token — sometimes worse than normal text, because garbled
  character sequences can tokenize *less* efficiently than clean words.
- **Meaning problem (the real one):** embedding and LLM models learned
  patterns from real, well-formed language. Feed them a mangled
  sentence (columns interleaved, a word cut mid-way) and they don't
  refuse — they just produce a vector or an answer that's subtly wrong,
  because they're pattern-matching against something that isn't a real
  sentence. This is silent: no crash, no error, just gradually worse
  results. That's why it's not "garbage in, garbage out" (obvious, loud
  failure) but "garbage in, garbage *embedding*" (quiet,
  hard-to-detect failure).

So `cleaners.py` isn't just tidying whitespace for cosmetics — it's
protecting both your token budget and the model's ability to actually
understand the text.
