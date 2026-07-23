# Original spec (verbatim, as received 2026-07-22)

> Preserved unmodified for provenance. The implemented design deviates from
> this spec in documented ways — see [plan-v1.2.md](plan-v1.2.md), decision
> record D1–D9, for each deviation and its justification.

---

# TASK: Install the deterministic-detector harness (7 items)

You are installing tooling that mechanizes environmental reflexes this project's
AI agents don't have. Work through the items IN ORDER. For each item: install,
verify with the listed acceptance check, and record evidence (actual command
output, not claims) in a final report. If an item fails, stop that item, report
honestly, and continue to the next — do not fake green.

## Item 0 — Recon (do first)
- Identify: repo root, Python env/venv in use, how the test suite is invoked
  (pytest args, config in pyproject.toml / pytest.ini / setup.cfg), where the
  Cleanroom/CI gate scripts live, and whether `.claude/settings.json` and
  `CLAUDE.md` exist at repo root.
- Report what you found before proceeding. Adapt all commands below to the
  real layout (e.g., `uv pip install` vs `pip install`, actual test dir name).

## Item 1 — pytest-randomly (test-order randomization)
- Install `pytest-randomly` into the project's test environment and add it to
  dev dependencies (pyproject/requirements — wherever this project pins them).
- No config needed; it auto-activates.
- ACCEPTANCE: run a small subset of the suite twice and show that the
  pytest header prints `Using --randomly-seed=...` with different seeds.
- Append to CLAUDE.md under a `## Test discipline` section:
  "Test failures that appear/disappear across runs are order-dependence, not
  flakes. Do not retry them away. Reproduce with
  `pytest -p randomly --randomly-seed=<seed from failing run>`, then run
  detect-test-pollution (see below)."

## Item 2 — detect-test-pollution (pollution bisection)
- Install `detect-test-pollution` into the same env; add to dev deps.
- Do NOT run a full bisection now (it's slow); this is an on-failure tool.
- ACCEPTANCE: `detect-test-pollution --help` runs clean in the project env.
- Append to CLAUDE.md:
  "When randomization surfaces an order-dependent failure, do not debug by
  reading code first. Run:
  `detect-test-pollution --failing-test <nodeid> --tests <testdir>/`
  and let it name the polluter pair. Fix the polluter, not the victim."

## Item 3 — Diff-scoped mutation testing in the gate
- Install `mutmut`; add to dev deps.
- Create `scripts/mutation_gate.sh` (executable), adapting paths to this repo:

      #!/usr/bin/env bash
      set -euo pipefail
      BASE="${1:-origin/main}"
      CHANGED=$(git diff --name-only "$BASE"...HEAD -- '*.py' | grep -v '^tests/' || true)
      if [ -z "$CHANGED" ]; then echo "No non-test .py changes; mutation gate PASS (vacuous)"; exit 0; fi
      PATHS=$(echo "$CHANGED" | paste -sd, -)
      mutmut run --paths-to-mutate "$PATHS"
      mutmut results
      # Fail if any mutant survived
      if mutmut results | grep -qE 'survived'; then
        echo "MUTATION GATE: FAIL — surviving mutants in changed code (test theater)"; exit 1
      fi
      echo "MUTATION GATE: PASS"

- Check mutmut's current CLI (its flags have changed across major versions —
  read `mutmut --help` and the installed version's docs) and adjust the script
  so it actually works. Verify the survived-detection grep matches real output.
- Wire `scripts/mutation_gate.sh` into the existing Cleanroom/gate script as a
  required step, same severity as a failing test.
- ACCEPTANCE: demonstrate the gate end-to-end on a throwaway branch:
  make a trivial code change with a deliberately weak test, show a surviving
  mutant fails the gate; then strengthen the test and show it passes. Include
  the real output of both runs in the report. Delete the throwaway branch.

## Item 4 — Claude Code hooks (unskippable lint/format)
- First read the CURRENT Claude Code hooks documentation (env var names and
  schema have evolved — verify `$CLAUDE_FILE_PATHS` or its current equivalent,
  and current matcher syntax). Then create/merge `.claude/settings.json`:

      {
        "hooks": {
          "PostToolUse": [{
            "matcher": "Edit|Write|MultiEdit",
            "hooks": [{
              "type": "command",
              "command": "ruff format --check $CLAUDE_FILE_PATHS && ruff check $CLAUDE_FILE_PATHS"
            }]
          }]
        }
      }

- If `.claude/settings.json` already exists, MERGE — do not clobber existing
  hooks or permissions.
- Scope the command so it only fires on .py files if the hooks schema supports
  it; otherwise guard inside the command.
- ACCEPTANCE: edit a scratch .py file with a deliberate format violation via
  Claude Code and show the hook blocks with ruff's stderr; then fix and show
  it passes. Clean up the scratch file.

## Item 5 — Worktree-per-agent rule
- Append to CLAUDE.md under `## Concurrency discipline`:
  "Never run `git checkout` or `git switch` in the main clone while any worker
  or subagent is active. Each concurrent agent gets its own worktree:
  `git worktree add ../<repo>-<agent> <branch>`. Branch switching in a shared
  tree is a gate-level violation."
- ACCEPTANCE: show the CLAUDE.md diff.

## Item 6 — Blast-radius code graph (MCP)
- Install CodeGraph (MIT, local, SQLite-backed) per its current README, index
  this repo, and register it with `claude mcp add` at project scope.
  If CodeGraph proves unsuitable for this codebase, fall back to
  code-review-graph and say why you switched.
- ACCEPTANCE: query the graph for the callers + dependent tests of one real,
  nontrivial function in this repo and include the output.
- Append to CLAUDE.md under `## Change discipline`:
  "Before modifying any function, query the code graph for its callers and
  dependent tests and paste the result into your plan. A plan without a
  blast-radius query is incomplete."

## Item 7 — Failed-gate-to-memory (LESSONS.md)
- Create `LESSONS.md` at repo root with a one-line header explaining its
  purpose (append-only log of gate failures and root causes).
- Add to the gate script: on any red, append a line
  `- [<date>] <failing check>: <one-line cause>` to LESSONS.md.
- Append to CLAUDE.md: "Read LESSONS.md at the start of every session."
- ACCEPTANCE: trigger one intentional gate failure and show the appended line.

## Final report (required)
Produce a table: item | status (PASS / FAIL / PARTIAL) | evidence (verbatim
command output snippet). No item may be marked PASS without its acceptance
check having actually run. Anything you could not verify gets PARTIAL with an
honest note. List every file you created or modified, with diffs for CLAUDE.md
and .claude/settings.json.
