from pathlib import Path

import pytest
from pytest_examples import CodeExample, EvalExample, find_examples

ROOT = Path(__file__).parent.parent


@pytest.mark.parametrize(
    "example", find_examples(ROOT / "docs", ROOT / "README.md"), ids=str
)
def test_docs_linting(example: CodeExample, eval_example: EvalExample):
    if eval_example.update_examples:
        eval_example.format(example)
        eval_example.run_print_update(example)
    else:
        # eval_example.lint(example)
        eval_example.run(example)
        eval_example.run_print_check(example)
