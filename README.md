# efficient-ally
sys lab project 

              _＿_
            ／＞　  フ
            | 　_　_| 
          ／` ミ＿xノ 
         /　　　　 |
        /　 ヽ　　 ﾉ
        │　　|　|　|
    ／￣|　　 |　|　|
    | (￣ヽ＿_ヽ_)__)
    ＼二)

efficient-ally reads Python code and finds patterns that make it slower than it
needs to be, like searching a list inside a loop or building a string with `+=`.
For each one it explains the problem, shows the big-O before and after, and
suggests a concrete rewrite. The goal is a website where anyone can paste code
and get these suggestions; see [ROADMAP.md](ROADMAP.md) for the six-month plan.

## Quick start

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

efficient-ally examples/slow_examples.py          # human-readable report
efficient-ally examples/slow_examples.py --json   # the format the website will use
pytest                                            # run the tests
python tests/test_corpus.py                       # score the estimator on the corpus
ruff check . && ruff format .                     # lint and format
```

Example output:

```
examples/slow_examples.py:20:12: Linear search inside a loop [list-membership-in-loop]
    `seen` is a list, so `item not in seen` compares against its items one at a time, which
    takes O(len(seen)). It runs on every iteration of the for loop on line 19, so in total
    it costs O(len(items) * len(seen)).
    Suggestion: Keep a set with the same items as `seen`: create it wherever `seen` is
    assigned, and add to it wherever you append to `seen`. ...
    Complexity: O(len(items) * len(seen)) -> O(len(items))
    Suggested change:
      @@ -17,6 +17,8 @@
           seen = []
      +    seen_set = set()
           result = []
           for item in items:
      -        if item not in seen:
      +        if item not in seen_set:
                   seen.append(item)
      +            seen_set.add(item)
                   result.append(item)
```

## How it works

```
source ─▶ ProgramModel ─▶ rules ─▶ findings ─┐
             │                               ├─▶ Report (text or JSON)
             └────────▶ estimator ─▶ big-O ──┘
```

| File | What it does |
|---|---|
| `src/efficient_ally/model.py` | Parses the code and records, for every syntax node, its scope and the loops that repeat it. Guesses variable kinds (list, set, str, …), conservatively. |
| `src/efficient_ally/complexity.py` | Symbolic big-O values like `O(len(a) * len(b))`, and an estimator that derives them from loop structure. |
| `src/efficient_ally/rules/` | One file per pattern. Each rule yields `Finding`s with an explanation, before/after big-O, and optional `Edit`s. |
| `src/efficient_ally/analyzer.py` | `analyze(source)`: runs everything and returns a `Report`. |
| `src/efficient_ally/cli.py` | The `efficient-ally` command. |
| `examples/slow_examples.py` | One slow function per pattern on the roadmap, detected or not yet. |
| `tests/` | Unit tests. Rewrite tests run the original and the rewritten code and check they give the same answer. |
| `tests/corpus/` | Hand-labeled slow/fast programs with their true big-O, scored by `tests/test_corpus.py`. See its [README](tests/corpus/README.md). |

## Adding a rule

1. Write tests first in `tests/test_rules.py`: code that should be flagged, code
   that shouldn't be, and (if the rule suggests a rewrite) a check that the
   rewritten code gives the same results as the original.
2. Create `src/efficient_ally/rules/<name>.py` with a `Rule` subclass. Set `id`
   and `title` and implement `check(model)`. Use `model.loops_of`,
   `model.kind_of`, and `model.references` rather than re-deriving them, and
   copy the structure of `string_concat.py`.
3. Add it to `ALL_RULES` in `src/efficient_ally/rules/__init__.py`.
4. Run it on real code to look for false positives before calling it done.
