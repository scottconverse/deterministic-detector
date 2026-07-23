# Deterministic-Detector Plugin — Implementation Plan

**Version:** v1.2 — 2026-07-22 (supersedes v1.1)
**Author:** Claude (Fable 5)
**Status:** BUILD-READY per auditor, pending Scott's pilot-repo confirmation
and go for P0. Nothing has been installed, no repos touched.

## Changelog v1.1 → v1.2

- **A4 (auditor): required-check flag is owner-only.** "Required" is a
  branch-protection/ruleset setting, not a workflow property — a workflow file
  cannot declare itself required. The flip is an **owner-performed manual
  step** (recipe provided in §3.5); a new guardrail states that an agent never
  creates, modifies, or removes required-status-check settings on its own
  initiative. This covers the mirror image of the existing "someone ticks the
  required box on the mutation job" risk: an agent *unticking* the randomized
  job's box would dissolve the entire enforcement architecture in one click.
- **A5 (auditor): burn-in before required.** The randomized-suite job starts
  **informational** and flips to required only after burn-in: five green runs
  across different seeds, or one deliberate pollution-hunt pass. Rationale: the
  pilot suite has never run in random order; latent pollution (the premise of
  this whole project) would otherwise block the first unrelated PR — real bug,
  wrong hostage. detect-test-pollution gets its first real outing during
  burn-in, not during someone's feature merge.
- **P0 addition (auditor implementation note):** diff-scoped mutation in
  Actions requires the base branch actually fetched (`fetch-depth: 0` or an
  explicit base fetch), or the diff comes up empty and the job passes
  vacuously. P0 verifies the fetch configuration; P3's weak-test demo must
  show the job *enumerated the changed files*, not merely that it ran green.

## Changelog v1.0 → v1.1 (retained)

- **A1:** CI enforcement lane added (GitHub Actions on the exact SHA,
  ubuntu-latest; dissolves the mutmut/Windows question; local lane demoted to
  optional convenience).
- **A2:** hook smoke re-check shipped in the plugin; re-run after client
  updates.
- **A3:** proportionality mapping in the dev-rigor-stack integration passage.
- Required-vs-advisory CI split (randomized = required *after burn-in, per A5*;
  mutation = non-required/informational, never promoted without a recorded
  decision).
- Smaller: P5 deliberate gate-failure trace check; recon confirms-or-adds ruff
  config; code-graph spike seeded with `tirth8205/code-review-graph` (verify,
  don't trust).

---

## TL;DR

Build the "deterministic-detector harness" (originally a 7-item install spec) as
a **standalone Claude Code plugin** containing a declarative ruff hook (with a
shipped smoke re-check), a bundled installer skill for the repo-side pieces
(pytest-randomly, detect-test-pollution, an *advisory* mutation lane), and a few
lines of standing instructions. **Load-bearing enforcement lives in CI**, not in
the agent's session: two GitHub Actions jobs per repo — randomized suite
(required *after an owner-flipped burn-in*) and mutation report (permanently
informational unless deliberately promoted). **Branch protection is owner-only
territory**; agents never touch required-status settings. Keep the plugin
**separate from dev-rigor-stack**; the stack gets a short proportionality-aware
passage telling it to consume the harness's outputs when present. Changes from
the original spec: mutation gate **advisory, not blocking**; LESSONS.md
**dropped**; code graph **deferred** pending an identification spike.
Estimated build cost ≈ 220–280k tokens, mechanical work delegated to cheap
models via Workflow.

---

## 1. Background

The source spec ("Install the deterministic-detector harness, 7 items") asks for
tooling that mechanizes reflexes AI agents don't reliably have: test-order
randomization, pollution bisection, mutation testing in the gate, unskippable
lint hooks, a worktree-per-agent rule, a blast-radius code graph, and a
gate-failure log. Its spec discipline is good (real acceptance checks, "don't
fake green", demonstrate-failure-first) and is retained wholesale. Its
*packaging* (append five sections to each repo's CLAUDE.md, imperatively merge
`.claude/settings.json` per repo) and some technical choices are not, for
reasons documented below.

Environment facts this plan is grounded in (verified this session):

- User-scope skills live at `C:\Users\Scott\.claude\skills\` — dev-rigor-stack,
  proof-gate, gauntletgate, coder-tdd-qa, antistall, audit-lite/team,
  visitor-audit, landing-page.
- No self-authored plugin exists yet; this would be the first.
- The existing precedent for "skill that installs hooks" is **antistall**, which
  installs imperatively into `~\.claude\hooks\` + `settings.json`. The backups
  directory shows six timestamped `settings.json.bak-*` files from that pattern —
  imperative merge churn is a real, observed cost on this machine.
- Host is Windows 11; WSL with a working Docker engine is available. Per A1,
  Linux-only tooling's load-bearing home is CI (ubuntu-latest), not this box.

---

## 2. Decision record

Deviations from (or refinements of) the original spec, with justification.

### D1 — Package as a plugin, not a skill
A plugin ships hooks declaratively: the ruff hook applies wherever the plugin
is enabled, with no per-repo `settings.json` merge and nothing for an agent to
clobber. Updates propagate by version bump instead of re-running an installer
in N repos. The observed settings.json backup churn from antistall's imperative
install is the concrete evidence. Repo-side pieces a plugin cannot ship (dev
dependencies, CI workflow, gate wiring) are handled by a skill **bundled inside
the plugin** — one distribution unit.
**Caveat:** first self-authored plugin on this machine; Phase 0 verifies the
current plugin manifest/hooks schema against live docs before anything is built.
**Constraint:** no standalone skill copy with the same name may remain installed
(duplicate skills resolve nondeterministically — known inventory finding).

### D2 — Separate from dev-rigor-stack; integrate by reference, proportionally
Three reasons for separation:
1. **Change cadence.** The stack is process doctrine; it changes rarely. The
   harness is glue over churning interfaces (mutmut CLI, hooks schema). Folding
   them in forces a stack release every time a tool flag drifts.
2. **Scope.** The stack is language-agnostic; the harness is Python-specific
   and repo-invasive.
3. **Optionality is one-directional.** Repos can want the stack without
   mutation testing; nothing wants mutation gating without process around it.

Integration is one short passage added to the stack's VERIFY/MERGE sections,
**scaled by the stack's own blast-radius classification** (A3):
- **Low** (docs/copy/trivial): hook feedback only; no detector evidence
  required.
- **Medium+**: a randomized-order pass (CI job green) is the test-evidence
  standard.
- **High / release gate**: the advisory mutation report must be *present in the
  gate output* (it still cannot solely red the gate).

Stack version bumps accordingly. This mapping keeps the harness consistent with
the verification-effort-by-blast-radius rule instead of running flat-rate.

### D3 — Mutation gate is ADVISORY, not blocking (change from spec)
- **Equivalent mutants exist.** Some mutations provably cannot change observable
  behavior; no test can kill them. A zero-survivor hard gate reds on legitimate
  code as a matter of course.
- **Interaction with the never-merge-red hard rule.** A gate that reds on noise
  plus a rule forbidding red merges equals blocked merges on noise.
The lane still runs, still names surviving mutants in changed code, still
appears in gate output — it cannot solely turn the gate red. **In CI the
mutation job is non-required/informational — never ticked as a required status
check.** Promotion to blocking is a deliberate later decision, revisited after
several pilot gates, and per D9 that flip is owner-performed anyway.

### D4 — CI is the load-bearing mutation lane; the local spike decides only convenience
The original v1.0 plan treated a Windows mutmut spike as the go/no-go for the
whole item. Wrong framing: the load-bearing lane was never going to be a
Windows desktop. The mutation job runs in GitHub Actions on ubuntu-latest,
where mutmut is at home. The Phase 0 spike still runs (current mutmut 3.x CLI
must be learned regardless, and the result decides whether an *optional local*
lane — native or WSL — is offered by the installer), but its verdict no longer
gates the item. The CI job diff-scopes mutation to files changed vs the base
branch; whole-repo mutation is out of scope (too slow for per-PR use).
**Vacuous-pass trap (v1.2):** diff-scoping requires the base branch fetched in
the Actions checkout (`fetch-depth: 0` or explicit base fetch) or the diff is
empty and the job greens without mutating anything. P0 verifies the checkout
configuration; P3's acceptance requires evidence the job enumerated the
changed files.

### D5 — The ruff hook is "forced feedback", not a "block" (correction to spec)
A `PostToolUse` hook fires **after** the write; a non-zero exit feeds ruff's
stderr back to the agent and forces a same-turn fix, but the edit has already
happened. That is the honest — and still valuable — behavior: the agent cannot
end a turn with unlinted Python it hasn't been confronted about. The auditor
confirmed this satisfies the original intent (the "block" wording was the
spec's error); a PreToolUse variant is not pursued — format-checking content
that doesn't exist yet is shape-wrong.
Implementation: hook entry is a small **Python** script (Windows-first, no bash
dependency) reading the current stdin-JSON hooks payload — the spec's
`$CLAUDE_FILE_PATHS` env-var form is treated as unverified until Phase 0 checks
current docs. Exit-0 fast paths for non-`.py` files and repos with no ruff
config keep it silent everywhere it doesn't apply, including inside Workflow
fan-outs.
**Consequence for recon:** the installer's recon step must confirm the target
repo has ruff config, or add a minimal one — otherwise the hook demos silence.

### D5a — Shipped smoke re-check (A2)
Install-time proof is not delivery proof: a Claude Code client update can
change the hooks payload and silently kill the hook. The plugin ships a smoke
invocation (`/install-detector smoke`): touch a scratch `.py` containing a
deliberate violation, confirm ruff's stderr comes back through the hook, clean
up. `instructions.md` notes it is re-run after client updates. A dead hook is
survivable by design (D5 keeps it non-load-bearing); a *silently* dead one is
not acceptable.

### D6 — Drop item 7 (LESSONS.md) entirely (change from spec)
"What went wrong and why" already has two homes: dev-rigor-stack's durable
project state and the session memory system. A third, repo-root, append-only
file means no home is authoritative. **Audit note accepted:** the claim that
gate failures already land in the stack's state files is currently *asserted,
not verified* — P5's pilot therefore includes one deliberate gate failure and
shows where its trace actually landed. If it lands nowhere, the fallback
activates: gate-failure lines are written into the stack's existing state file
(still not a new top-level file).

### D7 — Defer the code graph (item 6) to plugin v1.1, pending a spike
"CodeGraph (MIT, local, SQLite-backed)" does not unambiguously identify one
maintained project — the namespace is crowded with collisions. Committing v1.0
to an unidentified dependency is how the wrong thing gets installed. Phase 0
runs a bounded disambiguation-by-URL spike, seeded with the auditor-confirmed
candidate `tirth8205/code-review-graph` — a candidate to *verify* (license,
maintenance, fitness), not to trust. v1.0 of the plugin ships without the MCP
component; v1.1 adds it only if the spike names a concrete winner. The spec's
companion rule ("every function change requires a pasted blast-radius query")
is rejected regardless — always-on overhead contradicting
verification-effort-by-blast-radius. If the graph ships, its instruction is
scoped to non-trivial changes only.

### D8 — Near-zero standing-instruction footprint (change from spec)
The spec appends five sections to each target repo's CLAUDE.md — permanent
per-session context cost, multiplied across repos. Instead: the test-discipline
text (order-dependence ≠ flake; reproduce with the failing seed; run
detect-test-pollution) and the worktree-per-agent rule (item 5) live **once**,
in the plugin's own instruction file, kept to a few lines. Target repos get at
most one pointer line, and only if the pilot shows it's needed.

### D9 — Branch protection is owner-only; burn-in before required (A4 + A5, new in v1.2)
**Owner-only (A4).** "Required status check" lives in branch protection /
rulesets, not in any workflow file — and it is the single point where the
entire enforcement architecture concentrates. An agent with admin rights that
unticks one box removes everything the harness exists for. Standing rule,
mirrored in §7 guardrails: *an agent never creates, modifies, or removes
required-status-check settings on its own initiative.* Both flips (randomized
job → required at burn-in end; any future mutation-job promotion) are
owner-performed manual steps; the installer provides the recipe (§3.5) and
stops.
**Burn-in (A5).** The pilot suite has never run in random order; if latent
pollution exists — the premise of this project — a day-one required check takes
the first unrelated PR hostage for a months-old bug someone else planted. The
randomized job therefore starts informational and flips to required only after
**five green runs across different seeds, or one deliberate pollution-hunt
pass** (whichever comes first). Order-dependent failures found during burn-in
are detect-test-pollution's first real outing — fixed per the polluter-not-
victim rule, on their own PRs, before the check can hold anyone hostage.

---

## 3. What gets built

### 3.1 Plugin repository
New repo `deterministic-detector` (GitHub `scottconverse/`; created private,
flipped public after final review — no secrets, no handoffs, no internal
briefs). Layout (exact filenames confirmed against live plugin docs in P0):

```
deterministic-detector/
  .claude-plugin/plugin.json        # manifest: name, version, description
  hooks/hooks.json                  # PostToolUse on Edit|Write|MultiEdit
  hooks/ruff_feedback.py            # stdin-JSON reader; .py-only; exit-0 fast paths
  skills/install-detector/SKILL.md  # repo-side installer incl. `smoke` mode (3.2)
  ci/detectors.yml                  # template GitHub Actions workflow (3.3)
  instructions.md                   # test discipline + worktree rule + smoke-after-update note
  README.md                         # what it is, what it deliberately isn't
```

### 3.2 Bundled installer skill (`/install-detector`)
Runs per target repo. Steps, preserving the original spec's recon-first and
evidence rules:

1. **Recon** — repo root, venv/env manager (`uv` vs `pip`), test invocation,
   where the gate scripts live, CI provider, **ruff config present-or-added**.
   Report before changing anything.
2. **pytest-randomly** — install, pin in the repo's dev-deps file. Acceptance:
   two runs of a small suite subset showing two different
   `Using --randomly-seed=...` headers, verbatim.
3. **detect-test-pollution** — install, pin. Acceptance: `--help` runs clean in
   the project env. (On-failure tool; never run a full bisection at install.)
4. **CI detector jobs** — instantiate `ci/detectors.yml` in the repo (A1):
   randomized-suite job (seed recorded in the log) and diff-scoped mutation
   report job. **Both start informational** (D9). Acceptance: both jobs run on
   a real PR SHA; the mutation job's log shows the changed files it mutated
   (non-vacuous). The installer then **prints the owner recipe (§3.5) and
   stops** — it never touches branch protection.
5. **Optional local mutation lane** — only per the D4 spike verdict; wired as
   an advisory reporter. Acceptance: throwaway-branch demo — a deliberately
   weak test shows a surviving mutant reported as ADVISORY; strengthening the
   test clears it; both outputs verbatim; branch deleted. (If no local lane:
   the same demo runs through the CI job instead.)
6. **Smoke mode** (`/install-detector smoke`, per D5a) — scratch `.py` with a
   violation → hook stderr shown → cleanup. Also the post-client-update
   re-check.
7. **Final report** — item | PASS/FAIL/PARTIAL | verbatim evidence; every file
   created or modified, with diffs. No PASS without its check having run.
   Burn-in status (runs so far, seeds seen) included.

### 3.3 CI workflow template (`ci/detectors.yml`)
Two jobs, GitHub Actions, instantiated per repo by the installer:
- **randomized-suite** — full suite under pytest-randomly on ubuntu-latest,
  seed printed and preserved in the job log for reproduction. Starts
  **informational**; flips to **required** only by owner action after burn-in
  (D9): five green runs across different seeds or one deliberate
  pollution-hunt pass.
- **mutation-report** — mutmut pinned by version, diff-scoped to files changed
  vs the base branch (checkout with `fetch-depth: 0` or explicit base fetch —
  see the D4 vacuous-pass trap), surviving mutants listed in the job summary.
  **Non-required / informational, permanently** unless deliberately promoted
  by the owner with a recorded stack decision. The workflow file carries a
  comment stating both rules so the intent survives the plan document.
Enforcement therefore runs on the exact SHA, on a machine no agent controls —
outside the agent boundary, which is the property the whole harness exists for.

### 3.4 dev-rigor-stack update
The D2 proportionality passage added to
`C:\Users\Scott\.claude\skills\dev-rigor-stack\SKILL.md`, version bumped,
change pushed per the stack's normal release process. Acceptance: the diff
(P4), exercised for real in P5.

### 3.5 Owner recipe — flipping the randomized job to required (manual, one-time per repo)
Performed by Scott, never by an agent (D9). Either route:
- **GitHub UI:** repo → Settings → Branches (or Rules) → edit the default-branch
  protection rule → "Require status checks to pass" → add the
  `randomized-suite` check → save.
- **CLI (one command, run as yourself):**

```bash
gh api repos/scottconverse/<REPO>/branches/main/protection/required_status_checks/contexts -X POST -f "contexts[]=randomized-suite"
```

The installer prints this recipe with the real repo name filled in, alongside
the burn-in status, and takes no further action.

---

## 4. Build phases and acceptance evidence

| Phase | Work | Acceptance (evidence required) |
|---|---|---|
| **P0 Spike** | Verify current plugin manifest + hooks stdin schema from live docs; learn mutmut 3.x CLI + attempt local run (decides *optional* local lane only); **verify Actions checkout config for diff-scoping (fetch-depth trap)**; code-graph disambiguation-by-URL seeded with `tirth8205/code-review-graph`, license + maintenance checked | Spike notes with verbatim outputs; verdicts recorded; plan bumped to v1.3 |
| **P1 Plugin core** | Repo, manifest, ruff hook, smoke mode, instructions.md; install plugin locally | Real Claude Code edit of a scratch `.py` with a violation → hook stderr verbatim → fixed → clean pass; then the same proof via `/install-detector smoke`; scratch cleaned |
| **P2 Installer + CI** | `/install-detector` steps 1–4 (recon, randomly, pollution, CI jobs, both informational); installer prints the §3.5 owner recipe | Installer acceptance outputs from the pilot repo, incl. both CI jobs on a real PR SHA; **owner flip of the randomized job happens only after A5 burn-in completes, by Scott, per the recipe** |
| **P3 Mutation lanes** | CI mutation job proven with the weak-test/strong-test demo; optional local lane per P0 verdict | Throwaway-branch demo outputs verbatim: job log **enumerates the changed files it mutated** (non-vacuous), surviving mutant reported ADVISORY → strengthened test clears it; branch deleted |
| **P4 Stack integration** | D2 proportionality passage; stack version bump | Diff of the stack SKILL.md |
| **P5 Pilot + report** | Full install on the pilot repo; burn-in tracked (seeds logged); **one deliberate gate failure to locate its trace (D6 check)**; final report table | Report per 3.2 step 7, incl. burn-in status and where the gate-failure trace landed (or activation of the D6 fallback) |

Failure handling is the spec's own rule: an item that fails stops, reports
honestly with the real output, and the run continues to the next item.

**Pilot repo — recommendation:** TinkerQuarry (Python, active, existing
GauntletGate discipline, GitHub-hosted CI available, and not the shared-lane
civiccast clone). Explicitly NOT piloted on civiccast while WS5 is being built
from another machine. Auditor endorses the reasoning; final repo choice is
Scott's call.

---

## 5. Execution and cost model

Per the standing budget-delegation rule: **Fable designs and reviews; Workflow
builds.** P0 spike and mechanical build steps run as Workflow subagents (sonnet
for spike/analysis, haiku for mechanical file generation); Fable reviews P0's
verdicts, the hook script, the CI template, and the final report. No bare Agent
fan-out.

Estimated total: **≈ 220–280k tokens** (spike 30–60k, build 120–180k incl. the
CI lane, review ~30k). Estimate, not measurement; actuals reported in the
final report. P0 alone (~30–60k) remains a useful standalone unit and a
natural pause point. Burn-in itself costs no agent tokens — it accrues on
ordinary PRs.

---

## 6. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Plugin/hooks schema drift vs my knowledge | Medium | P0 verifies against live docs before any code |
| Hook silently dies after a client update | Medium (over time) | D5a smoke re-check, documented as post-update routine |
| An agent modifies branch protection (either direction: unticking randomized, or promoting mutation) | Low, catastrophic if it happens | D9 owner-only rule in guardrails + workflow-file comment; flips are manual recipes, installer prints-and-stops |
| Day-one required check blocks an unrelated PR on latent pollution | High without A5 | A5 burn-in: informational until 5 green seeds or a pollution-hunt pass; polluters fixed on their own PRs first |
| Diff-scoped mutation passes vacuously (base not fetched) | Medium | P0 checkout verification + P3 acceptance requires enumerated changed files |
| mutmut CLI churn breaks the CI job | Medium | Version pinned in the workflow; diff-scoped runs keep failures cheap to debug |
| Hook noise slows Workflow fan-outs | Low | .py-only + no-config fast exit; ruff is milliseconds per file |
| Duplicate-skill nondeterminism if an old copy lingers | Low | Single distribution unit; uninstall check in P5 |
| Code-graph spike picks an unmaintained tool | Medium | Disambiguation-by-URL + license/maintenance check; deferral means plugin v1.0 carries no such risk |
| Advisory lane ignored forever | Medium | D2 proportionality makes it *required-present* at high/release blast radius; promotion revisited after several pilot gates |
| Pilot destabilizes an active repo | Low | Pilot on TinkerQuarry; installer is additive; only new CI jobs and deps, no existing gate steps modified |

---

## 7. Guardrails (things this plan explicitly will not do)

- **No agent ever creates, modifies, or removes required-status-check /
  branch-protection settings on its own initiative (D9).** Flips are
  owner-performed via the §3.5 recipe, in both directions.
- No writes to any repo's `.claude/settings.json` (the plugin makes it moot).
- No CLAUDE.md appends beyond at most one pointer line in the pilot repo.
- No touching `claude/ws5-supervisor` or building civiccast from this machine.
- No `git add -A`; exact-path staging only.
- Plugin repo pushed on first commit and every commit (push-first rule); this
  plan document stays local (local-handoffs-stay-local rule).
- No installers/models/large artifacts committed anywhere.
- No completion claim without the phase's listed evidence having actually run.

---

## 8. Question status

1. **Pilot repo** — TinkerQuarry recommended; auditor endorses the reasoning;
   **awaiting Scott's confirmation.**
2. **mutmut lane** — RESOLVED (A1): CI-primary on ubuntu-latest; local/WSL
   optional per the P0 spike verdict.
3. **Repo visibility** — RESOLVED: private → public after final review.
4. **Code graph** — RESOLVED: run the P0 spike, seeded with
   `tirth8205/code-review-graph`; verify, don't trust.
5. **Item 4 semantics** — RESOLVED: forced same-turn feedback satisfies the
   original intent; no PreToolUse variant.
6. **A4/A5** — RESOLVED (v1.2): owner-only branch protection with printed
   recipe; burn-in before required.

**Remaining before build starts:** Scott's confirmation of the pilot repo and
the go for P0. (The §3.5 required-flip happens much later, after burn-in.)

---

## 9. Files to be created/modified (complete list)

**Created:** the plugin repo and contents per §3.1 (incl. `ci/detectors.yml`
and smoke mode); the instantiated CI workflow in the pilot repo; scratch/spike
files confined to the session scratchpad.
**Modified:** `C:\Users\Scott\.claude\skills\dev-rigor-stack\SKILL.md`
(proportionality passage + version bump, diff provided); pilot repo's dev-deps
file, CI config, and gate script (additive, diffs provided in the final
report).
**Modified by Scott only:** pilot repo branch-protection settings (§3.5
recipe, post-burn-in).
**Explicitly untouched by agents:** every repo CLAUDE.md except at most one
pointer line in the pilot repo; all `.claude/settings.json` files;
branch-protection/ruleset settings anywhere; anything under civiccast.
