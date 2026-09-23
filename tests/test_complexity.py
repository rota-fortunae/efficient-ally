import textwrap

import pytest

from efficient_ally import analyze
from efficient_ally.complexity import ONE, Complexity


def complexity_of(source: str, function: str = "f") -> str:
    report = analyze(textwrap.dedent(source))
    return str(next(s.complexity for s in report.functions if s.name == function))


def test_adding_keeps_only_the_fastest_growing_terms():
    n, m = Complexity.of("n"), Complexity.of("m")
    assert n + n * m == n * m
    assert ONE + n == n
    assert str(n + m) == "O(m + n)"


def test_formatting():
    assert str(ONE) == "O(1)"
    assert str(Complexity.of("n", "n")) == "O(n^2)"
    assert str(Complexity.of("a") * Complexity.of("b") + Complexity.of("c")) == "O(a * b + c)"
    assert str(Complexity.of("n", "n - i")) == "O(n * (n - i))"


@pytest.mark.parametrize(
    "text",
    [
        "O(1)",
        "O(n^2)",
        "O(len(a) * len(b) + n)",
        "O(len(nums) * log(len(nums)))",
        "O(2^n)",
        "O(2^(cols + rows))",
        "O(n * (n - i))",
        "O(? * len(tasks))",
    ],
)
def test_parse_reads_back_what_str_prints(text):
    assert str(Complexity.parse(text)) == text


def test_parse_ignores_order_and_simplifies():
    assert Complexity.parse("O(n * m + m)") == Complexity.of("m", "n")
    assert Complexity.parse("O(len(a)^2)") == Complexity.of("len(a)", "len(a)")


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param(
            """
            def f(n):
                return n * 2
            """,
            "O(1)",
            id="no loops",
        ),
        pytest.param(
            """
            def f(n):
                total = 0
                for i in range(n):
                    for j in range(n):
                        total += i * j
                return total
            """,
            "O(n^2)",
            id="nested range loops",
        ),
        pytest.param(
            """
            def f(a, b):
                for x in a:
                    print(x)
                for y in b:
                    print(y)
            """,
            "O(len(a) + len(b))",
            id="loops one after another add",
        ),
        pytest.param(
            """
            def f(a):
                for i in range(len(a)):
                    for j in range(i + 1, len(a)):
                        print(a[i], a[j])
            """,
            "O(len(a)^2)",
            id="triangular loop is still quadratic",
        ),
        pytest.param(
            """
            def f(n):
                for i in range(n + 1):
                    for j in range(10):
                        print(i, j)
            """,
            "O(n)",
            id="constants are dropped",
        ),
        pytest.param(
            """
            def f(a, d):
                for i, x in enumerate(a):
                    for key, value in d.items():
                        print(i, x, key, value)
            """,
            "O(len(a) * len(d))",
            id="enumerate and dict.items",
        ),
        pytest.param(
            """
            def f(a, b):
                return [x * y for x in a for y in b]
            """,
            "O(len(a) * len(b))",
            id="comprehension with two for clauses",
        ),
        pytest.param(
            """
            def f(a, b: list):
                for x in a:
                    if x in b:
                        print(x)
            """,
            "O(len(a) * len(b))",
            id="membership test on a list is linear",
        ),
        pytest.param(
            """
            def f(n):
                while n > 1:
                    n //= 2
            """,
            "O(?)",
            id="while loop bounds are unknown for now",
        ),
        pytest.param(
            """
            def f(a):
                def g():
                    for x in a:
                        print(x)
                return g
            """,
            "O(1)",
            id="defining a nested function is free",
        ),
    ],
)
def test_estimate(source, expected):
    assert complexity_of(source) == expected


def test_rule_findings_feed_into_the_estimate():
    # The loops alone say O(len(words)), but the string copying makes it quadratic.
    source = """
        def f(words):
            s = ""
            for w in words:
                s += w
            return s
    """
    assert complexity_of(source) == "O(len(words)^2)"
