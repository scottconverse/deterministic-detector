# deterministic-detector

**Website: [scottconverse.github.io/deterministic-detector](https://scottconverse.github.io/deterministic-detector/)**

A Claude Code plugin that gives an AI coding agent a few reflexes it doesn't
reliably have on its own: catching lint/format problems in the same turn,
running tests in randomized order instead of a fixed order that can hide
order-dependent bugs, and reporting (not gating on) surviving mutants in
changed code.

It's meant for repos where an AI agent is doing real editing — the kind of
place where "the tests passed" can quietly mean "the tests passed in the one
order they happen to be written in."

## What it is

- A **ruff hook** that fires right after any `Edit`/`Write`/`MultiEdit` on a
  `.py` file and feeds ruff's format/lint output back to the agent in the
  same turn, if the repo has ruff configured.
- An **`/install-detector` skill** that wires the repo-side pieces into a
  target repo: `pytest-randomly`, `detect-test-pollution`, and two GitHub
  Actions jobs (a randomized-order test run, and a diff-scoped mutation
  report).
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
out of a check. Even there, only the randomized-order job is ever a required
status check, and only after the repo owner manually flips it once the suite
has proven itself clean across several different random orders (burn-in).
No agent ever touches branch-protection or required-status-check settings,
in either direction — that's an owner-only action, always.

## Install

Add this plugin to Claude Code, then in the target repo run
`/install-detector`. It recons the repo first and reports before changing
anything. Run `/install-detector smoke` after any Claude Code client update
to confirm the hook still works.

On a machine that has never run the graph tool, pre-warm the uvx cache once
before your first session with the plugin — otherwise the code-graph MCP
server's first spawn includes a package download and can miss the client's
connection window (one session, self-heals after):

    uvx --from code-review-graph==2.3.7 code-review-graph --version

## Full design record

See [`docs/plan-v1.2.md`](docs/plan-v1.2.md) for the complete decision
record, phased build plan, and risk register behind this plugin.
