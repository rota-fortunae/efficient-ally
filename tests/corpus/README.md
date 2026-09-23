# Corpus

Hand-labeled programs used to measure the analyzer. `tests/test_corpus.py`
checks the analyzer against them, and `python tests/test_corpus.py` prints a
scoreboard.

Each file has:

- a docstring saying what the code does and which pattern it shows;
- either a `slow` and a `fast` version, or a single function for code that's
  already fine. Each function has an `# expect: O(...)` comment with its true
  worst-case running time;
- `EXAMPLES`: tuples of arguments. The tests run every function on each one and
  check that all versions return the same result.

## Writing expectations

- **Write the real complexity, not what the analyzer says.** If the analyzer
  disagrees, add the function to `KNOWN_MISSES` in `tests/test_corpus.py` with
  the reason. Never "fix" an expectation to match the analyzer.
- **Annotate parameter types** (`items: list[int]`). Without them the true
  complexity depends on what the caller passes (a list or a set?).
- **Use the function's parameters and the analyzer's notation:**
  - `n` for a number parameter named `n`; `len(items)` for the size of a
    collection parameter; `len(row)` for the size of the inner items of a
    nested collection (like the rows of a grid);
  - `log(n)`, `2^n`; multiply with ` * `, integer powers with `^`, add with ` + `.
- **Drop constants and lower-order terms**, as usual for big-O: `O(n^2)`, not
  `O(n^2 + n)`. Keep terms that neither dominates: `O(len(a) + len(b))`.
- **Assumptions:** arithmetic is O(1); set and dict operations are O(1) (the
  usual average case); strings and dict keys are short unless their length is
  part of the problem.

## Adding programs

The programs here are textbook and LeetCode-style problems. The most valuable
additions are real code: your own old assignments, or classmates' code (ask
first). That's what the website will see, and it contains patterns a textbook
wouldn't think of.
