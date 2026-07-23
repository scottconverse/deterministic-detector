# Self-hosting pilot report — 2026-07-23

Phases P2 (installer), P3 (weak/strong mutation demo), P5 (pilot + burn-in) and
P4 (stack integration) of [plan-v1.2.md](plan-v1.2.md), executed on this repo
itself. The plugin-hook end-to-end check (smoke mode) had already passed in a
fresh session on 2026-07-22 and is not repeated here.

## Status table

| Item | Status | Evidence (verbatim) |
|---|---|---|
| Recon before changes | PASS | Reported: pip/venv, no tests, no pyproject, no CI, code already ruff-clean (`All checks passed!` / `1 file already formatted`) |
| Test suite exists & is real | PASS | 9 behavioral subprocess tests; sensitivity proven red-first: sabotaging the hook verdict (`return 2` → `return 0`) failed exactly the 3 verdict-bearing tests (`3 failed, 6 passed`), revert → `9 passed` |
| pytest-randomly two-seed acceptance | PASS | `Using --randomly-seed=4057780287` then `Using --randomly-seed=943215811`, both `9 passed` |
| detect-test-pollution acceptance | PASS | `detect-test-pollution --help` prints usage clean in the project venv |
| CI jobs on a real PR SHA ([PR #2](https://github.com/scottconverse/deterministic-detector/pull/2)) | PASS | Both jobs green on PR SHA; randomized log `Using --randomly-seed=499405493`; mutation job vacuous case correct for a YAML-only PR: `(no non-test .py files changed vs origin/main)` |
| Non-vacuous diff-scoping ([PR #3](https://github.com/scottconverse/deterministic-detector/pull/3)) | PASS | Scope step enumerated `demo_rules.py` in log + job summary |
| Weak test → survivors named | PASS | Run 29980062281 *(after fixes; first attempts documented below)*: `demo_rules.x_within_line_limit__mutmut_1: survived` / `__mutmut_2: survived` |
| Strong test → survivors cleared | PASS | Run 29980574182: `2/2  🎉 2` (both mutants killed); throwaway PR #3 closed unmerged, branch deleted |
| Burn-in (A5): 5 green runs, distinct seeds | PASS | workflow_dispatch runs 29980693671 / 29980696747 / 29980699725 / 29980702766 / 29980705974, all `completed/success`; seeds `2995375398, 965068483, 174766110, 1166805330, 1607599847` — 5 distinct |
| Branch protection untouched (D9) | PASS | No agent call touched protection settings; owner recipe printed below |
| P4 stack integration | PASS (scoped) | Proportionality passage added to the LIVE skill `~\.claude\skills\dev-rigor-stack\SKILL.md` under VERIFY (diff = the passage, quoted in the PR-less local edit; upstream repo is **frozen at v1.5.1**, so no upstream PR — see deviations) |
| Gate-failure trace lands somewhere (D6 check) | PARTIAL | The baseline-failure incident (below) served as the deliberate red: its trace landed in the CI job summary + this report + session memory. The stack's own state files were not exercised (no stack-driven unit ran during the pilot). D6 fallback remains available. |

## Defects found by the pilot (all fixed, merged in [PR #4](https://github.com/scottconverse/deterministic-detector/pull/4))

1. **Silent CI skip:** the ruff-dependent tests skipped on CI (`5 passed, 4
   skipped`) because ruff wasn't in `requirements-dev.txt`. The suite ran at
   half strength while looking green. Fixed by pinning `ruff==0.15.18`.
2. **mutants/-layout path break:** mutmut copies scoped sources into `mutants/`
   and runs the suite from inside it; `__file__`-relative hook resolution found
   nothing there, and Python's exit code for a missing script (2) perfectly
   mimicked a ruff-failure verdict. Baseline failed; mutants went unchecked.
   Fixed with an ancestor-walk anchor (both `__file__` and cwd).
3. **Fourth vacuous-pass class — unchecked baselines:** a `not checked` mutant
   list flowed into the survivors summary looking like data. The workflow (and
   the template) now shout `BASELINE FAILED: mutants were NOT evaluated` with
   the run-log tail whenever it happens — proven live during the pilot, twice.

## Deviations from the plan

- **P4 upstream:** plan 3.4 assumed the stack's "normal release process". The
  full stack repo is **frozen at v1.5.1** (superseded by dev-rigor-stack-lite),
  so the passage went into the live installed skill only, marked as a
  local-box-only addition. Whether the public **lite** product should gain
  detector-awareness is a product-scope decision for the owner — not taken here.
- **Skill-trigger path:** `/install-detector` as a slash command was exercised
  in the 2026-07-22 smoke session, not here (this session predates the plugin
  junction). This pilot executed the installer's documented steps directly.

## Owner action (the one step no agent performs — D9)

Burn-in is complete (5 green, 5 distinct seeds). To make randomized-suite a
required check on `main`, run as yourself:

    gh api repos/scottconverse/deterministic-detector/branches/main/protection -X PUT -f "required_status_checks[strict]=false" -f "required_status_checks[contexts][]=randomized-suite" -F "enforce_admins=false" -F "required_pull_request_reviews=null" -F "restrictions=null"

or via UI: Settings → Branches → add a protection rule for `main` → "Require
status checks to pass" → add `randomized-suite` (job names were made plain in
[PR #5](https://github.com/scottconverse/deterministic-detector/pull/5) so the
context matches exactly). mutation-report stays permanently informational.
Note: `main` currently has no protection rule at all, so this CREATES one —
which is why the UI route may be simpler than the API call.

## Cost note

All pilot work ran inline in the coordinating session (sequential, CI-bound —
no fan-out benefit); CI minutes on a public repo are free. Wall clock ≈ 35 min
including six Actions runs.
