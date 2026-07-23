---
name: install-detector
description: Install the deterministic-detector harness (pytest-randomly, detect-test-pollution, diff-scoped mutation CI, ruff hook smoke check) into the current repo. Use when the user says "/install-detector", "install the detector harness", or asks to set up deterministic detectors, randomized test order, or mutation testing CI for this repo. Also handles "/install-detector smoke" to re-verify the ruff hook after a Claude Code client update.
---

# install-detector

Installs the repo-side pieces of the deterministic-detector harness. The ruff
hook itself ships with the plugin and needs no per-repo install; this skill
wires everything the plugin cannot ship declaratively. Full design record:
`docs/plan-v1.2.md` in the `deterministic-detector` plugin repo.

Every step reports evidence before moving on. No step is marked PASS without
having actually run. On failure: report honestly with the real output, then
continue to the next item (do not silently skip, do not fake green).

## Steps

1. **Recon.** Identify repo root, the env/package manager in use (`uv` vs
   `pip` vs `poetry`), how tests are invoked, where existing gate scripts
   live, the CI provider, and whether ruff config exists (`pyproject.toml`
   `[tool.ruff]`, `ruff.toml`, or `.ruff.toml`). If none exists, add a minimal
   one — the hook is silent without it. Report recon findings before changing
   anything.

2. **pytest-randomly.** Install and pin in the repo's dev-dependency file.
   Acceptance: run a small suite subset twice and show two different
   `Using --randomly-seed=...` headers, verbatim, side by side.

3. **detect-test-pollution.** Install and pin. Acceptance: `--help` runs
   clean in the project's environment. This is an on-failure tool — do not
   run a full bisection during install.

4. **CI detector jobs.** Instantiate `ci/detectors.yml` (from the plugin
   repo) into the target repo's `.github/workflows/`, adapted to the repo's
   dependency manager and test invocation from step 1. Both jobs start
   **informational** — never touch branch protection. Acceptance: both jobs
   run on a real PR SHA; the mutation job's summary shows it enumerated the
   changed non-test `.py` files (non-vacuous — the fetch-depth: 0 trap from
   plan D4). Then print the owner recipe below with the real repo name filled
   in, and **stop**.

   ```
   Owner action required (never performed by an agent):
   To require the randomized-suite check once burn-in is complete
   (5 green runs across different seeds, or one deliberate pollution-hunt
   pass), repo owner runs ONE of:

   GitHub UI: <repo> -> Settings -> Branches/Rules -> edit default-branch
   protection -> "Require status checks to pass" -> add "randomized-suite".

   CLI (run as yourself, not as an agent):
   gh api repos/<OWNER>/<REPO>/branches/main/protection/required_status_checks/contexts \
     -X POST -f "contexts[]=randomized-suite"

   mutation-report stays permanently informational unless you separately
   record a deliberate promotion decision.
   ```

5. **Code-graph index.** Build the repo's blast-radius graph:
   `uvx --from code-review-graph==2.3.7 code-review-graph build` from the repo
   root, and add `.code-review-graph/` to the repo's `.gitignore` (the index
   is a local artifact, never committed). Acceptance: run one real query —
   `code-review-graph query callers_of <a nontrivial function>` — and show
   its output; an ambiguous-name response resolved via `qualified_name`
   counts as pass. Traps (verified 2026-07-23): derive dependent tests from
   `callers_of` filtered to test nodes, NEVER from `tests_for` (it matches
   names, not calls, and under-reports ~20x); the tool needs a `.git` marker
   at the repo root; keep the `==2.3.7` pin — re-validate before any bump.
   Re-index after large changes with `... code-review-graph update`.
   If `uvx` is unavailable, install uv first (user scope) or skip with an
   honest note — the rest of the harness does not depend on this step.

6. **Optional local mutation lane.** Only offered if the plugin's P0 spike
   verdict allows a local (native or WSL) lane; otherwise skip and note why.
   If offered: acceptance is a throwaway-branch demo — a deliberately weak
   test shows a surviving mutant reported as ADVISORY, strengthening the test
   clears it, both outputs shown verbatim, branch deleted. If no local lane
   is offered, run the same weak/strong demo through the CI job instead.

7. **Smoke mode** (`/install-detector smoke`). Two checks. First, the
   code-graph MCP server: confirm this session has the plugin's `code-graph`
   tools (names like `...code-graph...query_graph_tool`). If absent, the
   likely cause is a cold uvx cache — the first-ever spawn downloads the
   package and can outrun the MCP client's connection window. Pre-warm it
   (`uvx --from code-review-graph==2.3.7 code-review-graph --version`), report
   the server as PENDING-RESTART, and note that the next session start is the
   real check. Then the hook: write a scratch `.py` file
   containing a deliberate ruff violation, edit it via the normal tool path,
   confirm the hook's stderr comes back to the agent, then delete the scratch
   file. This is also the prescribed re-check after any Claude Code client
   update — a client change to the hooks payload can silently kill the hook;
   this step is how that gets caught instead of assumed.

8. **Final report.** One line per item:

   ```
   item | PASS / FAIL / PARTIAL | verbatim evidence
   ```

   List every file created or modified with diffs. No PASS without its check
   having actually run. Include burn-in status (runs completed so far, seeds
   seen) for the randomized-suite job.
