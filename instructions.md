# deterministic-detector — standing instructions

**Test discipline.** Order-dependence is not flake. If a test fails only
under randomized order, reproduce it with the failing seed
(`Using --randomly-seed=...` from the log), then run `detect-test-pollution`
to find the polluter. Fix the polluter, not the victim — a passing-again
victim test with the polluter still in place is not a fix.

**Worktree per agent.** Never switch branches in a shared clone while other
agents may be active in it. Use a separate worktree (or clone) per
concurrently-running agent.

**Smoke after client updates.** Re-run `/install-detector smoke` after any
Claude Code client update. A payload-schema change can silently kill the
ruff hook; the smoke check is how that's caught instead of assumed.

**Branch protection (D9).** Agents never create, modify, or remove
required-status-check or branch-protection settings, in either direction —
not to require the randomized-suite job, not to promote the mutation job,
not to un-require anything. That is an owner-performed action only, via the
recipe `/install-detector` prints. See `docs/plan-v1.2.md` D9/A5.

**Blast radius (code graph).** For non-trivial changes in a repo with a
`.code-review-graph/` index, ground the blast-radius call with the code-graph
MCP tools before editing: `query_graph_tool` with `callers_of` (dependent
tests = callers filtered to `is_test`), or `get_impact_radius_tool` for a
changed-file view. Never use `tests_for` — it matches test names, not the
call graph, and under-reports badly. Ambiguous names return a candidate
list; re-query with the `qualified_name`. Re-index with
`build_or_update_graph_tool` after large changes. No index → skip silently;
trivial changes (docs, copy, typos) never require a graph query.
