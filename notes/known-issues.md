# Known Issues

Running list of known limitations discovered while building the pipeline —
not blocking, but worth remembering so we don't "rediscover" them later or
mistake them for new bugs.

---

## `ingestion/cleaners.py` — category-based filter can't catch every corrupted glyph

**What:** `clean()` filters characters by Unicode category (keeps
`L`/`N`/`P`/`Z` plus explicit exceptions like `\n` and `+`). This removes
most of the icon-font corruption from PDF extraction (`✉`, `♂`, `⌢`), but
not all of it — `¶` (PILCROW SIGN) still survives in the cleaned output
(e.g. `"¶obile+91..."`, corrupted from a phone icon glyph).

**Why it survives:** `¶`'s Unicode category is `Po` (Punctuation, other) —
the exact same category as real punctuation like `,` and `.`. The filter
has no signal to distinguish "a real comma" from "a corrupted icon glyph
that happens to also be classified as punctuation." This is a ceiling of
category-based filtering, not a bug — no amount of tweaking the current
approach fixes it, since the character itself gives no other clue about
its origin.

**Options considered:**
- Leave it — accept as a known limitation of the category-filter approach.
- Add a small, separate denylist of specific troublemaker characters
  observed during testing (`¶` and whatever else turns up), layered on
  top of the category filter rather than replacing it.

**Status:** left as-is for now (category filter only). Revisit if more
resumes surface more of these, or if a denylist becomes worth the
maintenance cost.
