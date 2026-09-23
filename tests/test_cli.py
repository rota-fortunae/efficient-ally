import json
import textwrap
from pathlib import Path

from efficient_ally.cli import main

EXAMPLES = Path(__file__).parents[1] / "examples" / "slow_examples.py"

DEDUPE = textwrap.dedent(
    """
    def dedupe(items):
        seen = []
        for item in items:
            if item not in seen:
                seen.append(item)
        return seen
    """
)


def test_text_output(tmp_path, capsys):
    path = tmp_path / "slow.py"
    path.write_text(DEDUPE)
    assert main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "[list-membership-in-loop]" in out
    assert "O(len(items) * len(seen)) -> O(len(items))" in out
    assert "+            seen_set.add(item)" in out


def test_json_output(tmp_path, capsys):
    path = tmp_path / "slow.py"
    path.write_text(DEDUPE)
    assert main([str(path), "--json"]) == 1
    [report] = json.loads(capsys.readouterr().out)
    assert report["functions"] == [
        {"name": "dedupe", "line": 2, "complexity": "O(len(items) * len(seen))"}
    ]
    assert report["findings"][0]["rule"] == "list-membership-in-loop"


def test_clean_file(tmp_path, capsys):
    path = tmp_path / "fine.py"
    path.write_text("def f(xs):\n    return sum(xs)\n")
    assert main([str(path)]) == 0
    assert "No inefficient patterns found." in capsys.readouterr().out


def test_syntax_error(tmp_path, capsys):
    path = tmp_path / "broken.py"
    path.write_text("def broken(:\n")
    assert main([str(path)]) == 2
    assert "error" in capsys.readouterr().err


def test_examples_file_is_analyzed(capsys):
    assert main([str(EXAMPLES)]) == 1
