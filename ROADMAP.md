# Roadmap

Six months, **October 2026 → March 2027**. Each month ends with a checkpoint you
can demo. If your school calendar is different, shift the dates but keep the
order: each month builds on the one before.

## Ground rules

- **Python first.** The `ast` module gives a full syntax tree for free, so the
  effort goes into analysis, not parsing. A second language is a stretch goal.
- **Precision over recall.** A tool that's wrong one time in five gets ignored.
  Rules stay quiet when unsure (for example, when they can't tell a variable is
  a list). False positives are tracked as a metric from month 3 on.
- **Every rewrite is tested by running it.** Tests execute the original and the
  rewritten code on the same inputs and compare results (see `tests/test_rules.py`).
- **The website never runs submitted code.** The analysis is static. Safely
  running untrusted code is a separate, much harder project.

## At a glance

| Month | Dates | Theme | Checkpoint |
|---|---|---|---|
| 0 | Sep 23–30 | Setup | ✅ Skeleton: program model, big-O algebra, loop estimator, 2 rules, CLI, CI |
| 1 | Oct | Foundations and test corpus | Estimator right on ≥ 80% of corpus functions (46% at the start, 72% now) |
| 2 | Nov | Loop analysis and local inefficiencies | `while` bounds, function calls, recursion, 3 new rules |
| 3 | Dec | Data-structure recommendations | All 9 patterns detected; < 10% false positives on real code |
| 4 | Jan | Rewrites you can trust | ≥ 5 rules with rewrites that pass differential tests; speedups measured |
| 5 | Feb | Website | Public URL; a 500-line file analyzed in < 1 s |
| 6 | Mar | Users, evaluation, presentation | ≥ 10 outside users, written evaluation, final demo |

---

## Month 1: Foundations and test corpus (October)

The skeleton works end to end. This month makes the foundations solid and
builds the test data everything else will be measured against.

- ✅ **Corpus and scoreboard** (done early, so there's a baseline to measure
  against). `tests/corpus/` covers all 9 patterns, loop analysis, and code
  that's already fine: 35 programs to start with, plus 9 with one obvious flaw
  each (sorting to find the max, `x in list(d.keys())`, re-summing inside a loop, …).
  Run `python tests/test_corpus.py` for the score. **Baseline: 30/65 right (46%).**
- **Week 1: learn the codebase.** Run `efficient-ally examples/slow_examples.py`
  and `python tests/test_corpus.py`, read `model.py` and `complexity.py`, and
  step through a test in a debugger. Background reading: *Green Tree Snakes* (a
  guide to Python's `ast` module) and the Python wiki's *TimeComplexity* page
  (the cost of built-in operations).
- **All month: add real code to the corpus.** The 35 programs are textbook-style.
  Add ≥ 10 from your own old assignments and classmates' code (with
  permission); see `tests/corpus/README.md`.
- The rest of the month works through `KNOWN_MISSES` in `tests/test_corpus.py`,
  biggest wins first (the scoreboard prints how many misses each kind of fix
  would clear):
  - ✅ **Weeks 1–2: operation costs** in `complexity.py`: `sorted` and `.sort()`
    (n log n), `set()`/`list()`/`Counter()`/`min`/`max`/`sum` of a collection,
    slicing, `+` on lists, `heapq` and `bisect`, string methods like `count` and
    `split`, and `in` on a slice. `log(n)` now counts as growing more slowly than
    `n`, so `O(n log n + n^2)` simplifies to `O(n^2)`. **Score: 60/83 (72%).**
    Not included yet: `+` on strings (the string rule handles loops) and
    `[0] * n`.
  - **Weeks 2–3: collection sizes and aliases (14 misses)** in `model.py`:
    `n = len(items)` means `n` *is* `len(items)`; `remaining = list(nums)` and
    `ordered = sorted(nums)` are as long as `nums`; a list that gets one `append`
    per iteration of a loop over `items` ends up at most `len(items)` long. Some
    of these showed up only once operation costs were counted: `"".join(lines)`
    is correctly charged `len(lines)`, but the analyzer can't tell that's `height`.
  - **Weeks 3–4: loop bounds (4 misses)** in `complexity.py`: a bound that
    depends on an outer loop variable (`for i in range(n): for j in range(i)`)
    is still at most `n`; `min(k, x)` is at most `k`; `range(n ** 2)` gives `n^2`.
  - **Week 4, if time allows: type inference** in `model.py`. `self.items = []`
    in `__init__` makes `self.items` a list in every method; `for row in grid`
    over a list of lists makes `row` a list.
- `while` loops and recursion (9 misses) are month 2.

**Checkpoint:** estimator right on ≥ 80% of corpus functions (fixing everything
above would give 74/83, or 89%); ≥ 10 real-code programs added; CI green.

## Month 2: Loop analysis and local inefficiencies (November)

- **`while` loop bounds** (currently shown as `?`):
  - counters: `while i < n: ... i += 1` gives `n`
  - halving or doubling: `n //= 2`, `i *= 2` gives `log n` (binary search!)
  - draining: `while stack: stack.pop()` gives `len(stack)`
- **Function calls:** build a call graph for the file. Calling a function inside
  a loop costs that function's complexity, with arguments substituted for its
  parameters.
- **Recursion:** recognize common recurrences. `f(n - 1)` gives O(n), `f(n // 2)`
  gives O(log n), and `f(n - 1) + f(n - 2)` gives O(2^n).
- **Local-inefficiency rules (pick at least 3):**
  - *Loop-invariant computation:* an expression inside a loop whose inputs don't
    change in the loop (`sorted(names)`, `len(data) * 2`, `re.compile(...)`)
    should be computed once, before the loop.
  - *Repeated allocation:* the same list, dict or set rebuilt on every iteration.
  - *Hidden copies in loops:* `a[:]`, `list(a)`, or `a = a + [x]` inside a loop.
  - *Missing early exit:* `for x in xs: if x == t: found = True` without `break`,
    which should use `any()` or `in`, or add a `break`.

**Checkpoint:** binary search, bubble sort and naive `fib` in the corpus get the
right big-O; 3 new rules, each with tests.

## Month 3: Data-structure recommendations (December)

One rule per pattern, each with at least 3 "flagged" tests, 3 "not flagged"
tests, and a rewrite test. Ordered by how often they show up in student code:

| # | Pattern | Detect (example) | Suggest | Status |
|---|---|---|---|---|
| 1 | Repeated linear search | `x in some_list` in a loop; `.index()`/`.count()` in a loop | set; dict of positions; `Counter` | ✅ `in` done (`list-membership-in-loop`) |
| 2 | Nested membership search | `[x for x in a if x in b]` | `set(b)`, or `set(a) & set(b)` | ✅ flagged by #1; add set-intersection wording |
| 3 | Repeated string concatenation | `s += piece` in a loop | `"".join(parts)` | ✅ done (`string-concat-in-loop`) |
| 4 | Repeated array shifting | `lst.pop(0)` / `lst.insert(0, x)` in a loop | `collections.deque` | ☐ |
| 5 | Nested search by key | `for a in A: for b in B: if a.id == b.id` | dict keyed by `id` | ☐ |
| 6 | Duplicate scanning | `for i: for j > i: if a[i] == a[j]` | set or `Counter` | ☐ |
| 7 | Repeated min/max search | `min(lst)` + `lst.remove(...)` in a loop | `heapq` | ☐ |
| 8 | Repeated sorting | `.sort()` / `sorted()` inside a loop | sort once, `bisect.insort`, or a heap | ☐ |
| 9 | Repeated expensive function | recursion with overlapping calls (`fib`) | `@functools.cache` | ☐ (needs month 2's call graph) |

- **Weeks 1–3:** rules 4–9, plus the rest of 1–2.
- **Week 4 (winter break, lighter):** *false-positive audit.* Run every rule on
  ≥ 2,000 lines of real, decent Python (parts of the standard library or a
  popular open-source project) and label every finding right or wrong. Fix or
  tighten any rule that is wrong more than 10% of the time.

**Checkpoint:** all 9 patterns detected in the corpus; < 10% false positives in the audit.

## Month 4: Rewrites you can trust (January)

- **Better rewrites.** Every rule that can produce `edits` does. Consider
  switching from line edits to [LibCST](https://libcst.readthedocs.io/), which
  keeps formatting and comments and can rewrite multi-line code.
- **Differential testing.** Use [Hypothesis](https://hypothesis.readthedocs.io/)
  to generate random inputs for each corpus program, run the original and the
  rewrite, and check they return the same results.
- **Measured speedups.** Time the original and rewritten code at n = 100, 1,000,
  10,000 and 100,000 and fit a line on a log-log plot. The slope is the measured
  exponent: "predicted O(n²) → O(n); measured 1.97 → 1.03" makes a strong slide
  for the final presentation.
- **Better explanations.** Have 3 classmates each read 10 explanations and point
  out anything confusing, then rewrite those.

**Checkpoint:** ≥ 5 rules with rewrites; all pass differential tests; measured
exponents within ±0.3 of the predictions on the corpus.

## Month 5: Website (February)

The website is a thin layer over `analyze()`. `Report.to_dict()`, which is what
`efficient-ally --json` prints, is already the API format.

- **Week 1: backend.** A [FastAPI](https://fastapi.tiangolo.com/) app in `web/`
  with `POST /api/analyze` returning `Report.to_dict()`. Guard against abuse:
  input ≤ 100 KB, a time limit (run the analysis in a worker process so one bad
  input can't hang the server), and per-IP rate limits. Never `exec` submitted code.
- **Week 2: frontend.** A code editor ([CodeMirror 6](https://codemirror.net/)),
  a table of big-O per function, findings with highlighted lines, before → after
  complexity, a diff of the suggested change, and a "copy fixed code" button.
- **Week 3: deploy.** Render, Fly.io, Railway, or a school server, with HTTPS.
  Add an examples dropdown filled from the corpus, and a 👍/👎 per finding that
  logs only the rule id and the vote (not the user's code).
- **Week 4:** buffer, phone layout, accessibility pass.

**Checkpoint:** public URL; a 500-line file analyzed in < 1 s; usable on a phone.

## Month 6: Users, evaluation, presentation (March)

- **Weeks 1–2:** get ≥ 10 people outside the project to try it on their own
  code (intro CS classes are ideal). Collect votes and run 3–5 short interviews.
  Fix the top complaints.
- **Week 3: evaluation write-up.** Precision/recall on the corpus, false-positive
  rate on real code, measured speedups, and a summary of user feedback.
- **Week 4:** final paper or poster, demo video, presentation.
- **Stretch goals (only if you're ahead):** JavaScript support via
  [tree-sitter](https://tree-sitter.github.io/); a VS Code extension that calls
  the same analyzer; a step-by-step "how we got this big-O" view.

---

## Weekly routine

- **Monday:** pick the week's goal from this file. Write the tests first: one
  program that should be flagged, one that shouldn't, and one that checks the
  rewrite runs correctly.
- **Friday:** commit, push, and add a few lines to `LOG.md` about what worked
  and what didn't. You'll want this when writing the final paper.
- **When you fall behind:** cut stretch goals first, then the lowest rows of the
  month 3 table. Don't cut tests.

## Known risks

| Risk | Mitigation |
|---|---|
| Big-O can't be computed exactly for arbitrary programs | Report what's known, show `?` for what isn't, and never pretend |
| Type guesses cause false positives | Conservative inference; stay quiet when unsure; month 3 audit |
| Rewrites change behavior (set ordering, duplicates) | Whitelist the uses a rewrite is safe for; differential tests |
| Website eats the schedule | Keep it a thin UI over `--json`; the analyzer is the product |
