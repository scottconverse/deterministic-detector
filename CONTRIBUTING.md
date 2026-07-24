# Contributing

## Set up

1. Clone the repository.
2. Install `uv`.
3. Create a development environment from `requirements-dev.txt`.

For an isolated test run without changing the repository environment:

```sh
uvx --from pytest==9.1.1 \
  --with pytest-randomly==4.0.1 \
  --with detect-test-pollution==1.2.0 \
  --with ruff==0.15.18 \
  pytest
```

## Validate a change

Run the full test suite, then check formatting and lint:

```sh
pytest
ruff format --check .
ruff check .
```

Changes to either host adapter must preserve the Claude and Codex package
contract tests in `tests/test_plugin_packaging.py`. Hook behavior changes must
start with a failing behavioral test in `tests/test_ruff_feedback.py`.

Open a pull request with the commands and complete result summaries you ran.
