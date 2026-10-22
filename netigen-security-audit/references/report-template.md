# Report template

The audit ends in a report the user reads before anything is fixed or filed. Full ranked list first. Keep it to evidence - every finding names a file and line and a concrete failure path. No secret values anywhere.

## Shape

```
# Security audit - <repos audited> - <date>

## Summary
<one paragraph: how many findings at each severity, the single most important one, and the overall posture>.

Scanners run: bandit, pip-audit, gitleaks, semgrep, ruff(S). Static hits triaged: <n> (<k> confirmed, <n-k> dropped as false positives).

## Findings (ranked by user impact)

### 1. <short title> - Critical
- **Repo / location:** netigen-draft - src/api/ownership.py:NN
- **Surface:** Authorization and ownership
- **Invariant:** <what must hold, from CLAUDE.md>
- **What breaks:** <the concrete path: this input reaches this sink without passing this check>
- **Impact:** <who is affected and how - e.g. a crafted message id reads another user's chat>
- **Fix direction:** <one line; the real fix is scoped later, or by bug-rca>
- **Ships in:** <repo that owns the flaw>

### 2. <title> - High
...

## Clean surfaces
<one line each for the surfaces that matched the model - e.g. "Delegated-token handling: token never reaches a log, block or tool argument (traced mcp_client -> registry). Clean.">

## Not audited here
<surfaces that live in another repo, e.g. link-preview SSRF is nexus; flag for a separate review>

## Dependency findings
<from sca-audit / pip-audit, if run - package, version, CVE, fixed-in, reachable y/n. These ship via sca-audit's flow>
```

## Rules for the report

- **List everything confirmed, passes included as "clean surfaces".** A report that shows only problems cannot be told from an audit that stopped early. State what you checked and found sound.
- **Rank by user impact**, not scanner severity. A bandit HIGH that is unreachable is a Low or a dropped hit; a MEDIUM-confidence authz gap that leaks another user's data is Critical.
- **One finding per real defect.** Do not split one bug across rows or pad the count to look thorough.
- **No secret values.** A secret finding names the file, line and that it is a secret, and says to rotate it - never the value.
- **Stop at the report.** Fixes and issues come after the user picks, in step 5 of the skill.

## After the user picks

- File issues (if asked) on the repo that ships the fix, `gh issue create`, titled by impact. Hand an issue number to `bug-rca` for the root cause and fix PR.
- Dependency bumps go through `sca-audit`.
- Respect each repo's branch/PR rules from its memory/CLAUDE.md (core commits to master with a tag; draft/mcp use a branch and PR; never commit on your own initiative).
