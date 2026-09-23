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
