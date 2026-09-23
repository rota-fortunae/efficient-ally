import pytest
from helpers import findings, rewritten, run

MEMBERSHIP = "list-membership-in-loop"
CONCAT = "string-concat-in-loop"


# --- list-membership-in-loop --------------------------------------------------


def test_unchanged_list_becomes_a_set_built_before_the_loop():
    source, found = findings(
        """
        def common(a: list[int], b: list[int]):
            out = []
            for x in a:
                if x in b:
                    out.append(x)
            return out
        """,
        MEMBERSHIP,
    )
    [finding] = found
    assert str(finding.current) == "O(len(a) * len(b))"
    assert str(finding.improved) == "O(len(a) + len(b))"

    fixed = rewritten(source, finding)
    assert "b_set = set(b)" in fixed
    assert "if x in b_set:" in fixed
    assert run(fixed, "common", [1, 2, 3, 2], [3, 2]) == run(source, "common", [1, 2, 3, 2], [3, 2])


def test_membership_inside_a_comprehension():
    source, found = findings(
        """
        def common(a: list[int], b: list[int]):
            return [x for x in a if x in b]
        """,
        MEMBERSHIP,
    )
    [finding] = found
    assert run(rewritten(source, finding), "common", [1, 2, 3], [3, 1]) == [1, 3]


def test_seen_list_gets_a_matching_set():
    source, found = findings(
        """
        def dedupe(items):
            seen = []
            result = []
            for item in items:
                if item not in seen:
                    seen.append(item)
                    result.append(item)
            return result
        """,
        MEMBERSHIP,
    )
    [finding] = found
    assert str(finding.current) == "O(len(items) * len(seen))"
    assert str(finding.improved) == "O(len(items))"

    fixed = rewritten(source, finding)
    assert "seen_set.add(item)" in fixed
    assert run(fixed, "dedupe", [3, 1, 3, 2, 1]) == [3, 1, 2]


def test_no_rewrite_when_the_list_changes_in_other_ways():
    _, found = findings(
        """
        def f(a: list, b: list):
            for x in a:
                if x in b:
                    b.remove(x)
            return b
        """,
        MEMBERSHIP,
    )
    [finding] = found
    assert finding.edits is None


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            """
            def f(a, allowed: set):
                return [x for x in a if x in allowed]
            """,
            id="already a set",
        ),
        pytest.param(
            """
            def f(a: list, x):
                return x in a
            """,
            id="not inside a loop",
        ),
        pytest.param(
            """
            def f(a, b):
                return [x for x in a if x in b]
            """,
            id="can't tell that b is a list",
        ),
        pytest.param(
            """
            def f(names: list):
                for key in ("a", "b", "c"):
                    if key in names:
                        print(key)
            """,
            id="loop runs a fixed number of times",
        ),
        pytest.param(
            """
            def f(selector, listener):
                while True:
                    ready = [key.fileobj for key in selector.select()]
                    if listener in ready:
                        print("ready")
            """,
            id="list is rebuilt before every search",
        ),
    ],
)
def test_membership_not_flagged(source):
    assert findings(source, MEMBERSHIP)[1] == []


def test_list_rebuilt_in_outer_loop_gets_set_before_inner_loop():
    source, found = findings(
        """
        def f(grid):
            hits = 0
            for row in grid:
                allowed = list(row[:2])
                for x in row:
                    if x in allowed:
                        hits += 1
            return hits
        """,
        MEMBERSHIP,
    )
    [finding] = found
    assert str(finding.current) == "O(len(allowed) * len(grid) * len(row))"
    assert str(finding.improved) == "O(len(allowed) * len(grid) + len(grid) * len(row))"
    fixed = rewritten(source, finding)
    assert "        allowed_set = set(allowed)\n        for x in row:" in fixed
    grid = [[1, 2, 1, 3], [4, 4, 5]]
    assert run(fixed, "f", grid) == run(source, "f", grid) == 5


# --- string-concat-in-loop ----------------------------------------------------


def test_augmented_concat_becomes_join():
    source, found = findings(
        """
        def join_words(words):
            s = ""
            for w in words:
                s += w + " "
            return s
        """,
        CONCAT,
    )
    [finding] = found
    assert str(finding.current) == "O(len(words)^2)"
    assert str(finding.improved) == "O(len(words))"

    fixed = rewritten(source, finding)
    assert 's_parts.append(w + " ")' in fixed
    assert run(fixed, "join_words", ["a", "b"]) == "a b "


def test_self_assignment_concat_is_detected_too():
    source, found = findings(
        """
        def shout(chars):
            out = ""
            for c in chars:
                out = out + c.upper()
            return out
        """,
        CONCAT,
    )
    [finding] = found
    assert run(rewritten(source, finding), "shout", "abc") == "ABC"


def test_string_reset_in_outer_loop_only_grows_in_inner_loop():
    source, found = findings(
        """
        def rows(grid):
            out = []
            for row in grid:
                line = ""
                for cell in row:
                    line += str(cell)
                out.append(line)
            return out
        """,
        CONCAT,
    )
    [finding] = found
    assert str(finding.current) == "O(len(grid) * len(row)^2)"
    assert str(finding.improved) == "O(len(grid) * len(row))"
    assert run(rewritten(source, finding), "rows", [[1, 2], [3]]) == ["12", "3"]


def test_no_rewrite_when_the_string_is_read_inside_the_loop():
    _, found = findings(
        """
        def f(words):
            s = ""
            for w in words:
                if len(s) > 10:
                    break
                s += w
            return s
        """,
        CONCAT,
    )
    [finding] = found
    assert finding.edits is None


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            """
            def f(xs):
                total = 0
                for x in xs:
                    total += x
                return total
            """,
            id="numbers, not strings",
        ),
        pytest.param(
            """
            def f(name):
                s = "hello "
                s += name
                return s
            """,
            id="not inside a loop",
        ),
        pytest.param(
            """
            def f(words):
                for w in words:
                    s = ""
                    s += w
                    print(s)
            """,
            id="string restarts every iteration",
        ),
        pytest.param(
            """
            def f(name):
                s = ""
                for part in ("Hello, ", name, "!"):
                    s += part
                return s
            """,
            id="loop runs a fixed number of times",
        ),
    ],
)
def test_concat_not_flagged(source):
    assert findings(source, CONCAT)[1] == []
