# deterministic-detector

**Website: [scottconverse.github.io/deterministic-detector](https://scottconverse.github.io/deterministic-detector/)**

A dual-compatible Claude Code and Codex plugin that gives an AI coding agent a
few reflexes it doesn't reliably have on its own: catching lint/format problems
in the same turn, running tests in randomized order instead of a fixed order
that can hide order-dependent bugs, and reporting (not gating on) surviving
mutants in changed code.

It's meant for repos where an AI agent is doing real editing — the kind of
place where "the tests passed" can quietly mean "the tests passed in the one
order they happen to be written in."

## What it is

- A **ruff hook** that fires right after Claude edits a `.py` file or Codex
  applies a patch to one, then feeds ruff's format/lint output back to the
  agent in the same turn, if the repo has ruff configured.
- An **`install-detector` skill** that wires the repo-side pieces into a
  target repo: `pytest-randomly`, `detect-test-pollution`, and three GitHub
  Actions jobs (a randomized-order test run, a diff-scoped mutation report,
  and a [tampercheck](https://github.com/scottconverse/tampercheck) lane
  that reads each PR's diff and fails if the change weakened the project's
  own verification — deleted/skipped/focused tests, `|| true`, hollowed
  assertions, swallowed errors).
- A **code-graph MCP server** (code-review-graph, pinned, run via `uvx` —
  nothing to install) answering "who calls this function, and which tests
  depend on it" from a local SQLite index the installer builds per repo.
  Grounds blast-radius calls in an enumerable answer instead of grep guesses.
- A short **instructions.md** covering test discipline, the blast-radius
  query rule, and a worktree-per-agent rule.

## What it deliberately is NOT

- **Not a mutation gate.** The mutation-report CI job is advisory by design,
  permanently. Equivalent mutants exist — mutations that provably can't
  change observable behavior, which no test can ever kill. A hard "zero
  survivors" gate reds on legitimate code as a matter of course. The job
  still runs, still lists what survived, still shows up in review — it just
  can't fail your build on its own.
- **Not a pre-write block.** The ruff hook runs *after* the edit already
  happened (`PostToolUse`), not before. It can't stop a bad edit from
  landing, but it can't let the agent walk away from one either — the
  failure comes back as forced, same-turn feedback.

## Where enforcement actually lives

Anything that can genuinely fail a build lives in CI, on a machine no agent
controls — not in the agent's own session, where an agent could talk itself
out of a check. Even there, only two jobs are ever candidates for required
status checks — randomized-suite (after burn-in across several random
orders) and tampercheck (after an observation period on real PRs; it is
installed pinned from PyPI so a locally edited copy cannot change what CI
enforces) — and both flips are performed manually by the repo owner, never
by an agent.
No agent ever touches branch-protection or required-status-check settings,
in either direction — that's an owner-only action, always.

## Requirements

- Python repository using pytest
- `ruff` available on the agent session's `PATH`
- [`uv`](https://docs.astral.sh/uv/) for the pinned code-graph MCP server
- GitHub Actions for the two CI detector jobs

## Install for Claude Code

Clone the plugin into Claude's skills directory, then start a new session:

```sh
git clone https://github.com/scottconverse/deterministic-detector \
  ~/.claude/skills/deterministic-detector
```

For a one-off session, use
`claude --plugin-dir ./deterministic-detector`.

## Install for Codex

Add this repository as a plugin marketplace:

```sh
codex plugin marketplace add scottconverse/deterministic-detector
```

Then open the Codex plugin browser, install **Deterministic Detector**, review
and trust its Ruff hook, and start a new session. In the ChatGPT desktop app,
restart the app and install it from the Plugins Directory.

## Wire a target repository

In the target repository, invoke `/install-detector` in Claude Code or
`$install-detector` in Codex. The skill recons the repo first and reports before
changing anything. Run the skill in `smoke` mode after either client updates to
confirm the hook and code-graph server still work.

On a machine that has never run the graph tool, pre-warm the uvx cache once
before your first session with the plugin — otherwise the code-graph MCP
server's first spawn includes a package download and can miss the client's
connection window (one session, self-heals after):

    uvx --from code-review-graph==2.3.7 code-review-graph --version

Claude and Codex use separate host manifests and hook declarations in this
repository, but share the same skill, MCP configuration, hook implementation,
CI template, and standing instructions. Host-specific adapters are tested
together so one host cannot drift silently from the other.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes are recorded in
[CHANGELOG.md](CHANGELOG.md). This project is available under the
[MIT License](LICENSE).

## Full design record

See [`docs/plan-v1.2.md`](docs/plan-v1.2.md) for the complete decision
record, phased build plan, and risk register behind this plugin.
