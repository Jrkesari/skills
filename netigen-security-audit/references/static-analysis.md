# Static analysis

Run every scanner with `uvx` so nothing is installed into the repos. Treat all output as **leads**: each hit is confirmed against the code and the threat model in step 3, or dropped with a one-line reason. A scanner's own severity is not the finding's severity - grade by user impact.

Run from each repo root. `$REPO` is one of netigen-draft, netigen-mcp, netigen-backend-core.

## bandit - Python security linter

```bash
uvx bandit -r . -ll -x ./tests,./.venv -f txt
```

- `-ll` reports medium+ confidence/severity; drop to `-l` for a fuller sweep when triaging.
- What it catches here: `subprocess`/`os.system` with shell, `eval`/`exec`, weak hashes, `yaml.load`, SQL built by string concat, `assert` used for a security check (stripped under `-O`), bind-all `0.0.0.0`, `requests` without timeout.
- Common false positives in these repos: `assert` in tests, `0.0.0.0` in the documented `uvicorn` run command, `subprocess` in scripts the service never imports. Drop these with a reason.

## pip-audit - vulnerable dependencies

Prefer the `sca-audit` skill (it reads the uv lockfile across all three repos and knows the report-first flow). If running directly:

```bash
uvx pip-audit -r <(uv export --format requirements-txt 2>/dev/null) 2>/dev/null \
  || uvx pip-audit  # falls back to the active environment
```

- Report each CVE with the package, installed version, fixed version, and whether the vulnerable path is actually reached.
- A dependency-only finding ships via `sca-audit`'s flow, not this skill's fixes.

## gitleaks - committed secrets

```bash
uvx gitleaks detect --source . --redacted --report-format json --report-path /tmp/gitleaks-$REPO.json
```

- `--redacted` keeps the secret value out of the report - keep it on.
- Scan **history**, not just the tree: a secret removed from HEAD is still in the pack. gitleaks scans history by default; confirm the commit range covers it.
- Report file, commit and rule - never the value. A real key means: rotate it (tell the user, do not do it for them), then scrub history is a separate decision.

If gitleaks is unavailable, fall back to detect-secrets:

```bash
uvx detect-secrets scan --all-files > /tmp/secrets-$REPO.json
```

## semgrep - taint patterns (optional, deeper)

```bash
uvx semgrep --config auto --severity ERROR --severity WARNING --timeout 120 .
```

- `--config auto` pulls the registry's Python/FastAPI rulesets - SSRF, injection, path traversal, missing auth, insecure deserialization.
- Slower and noisier; use when the manual pass flags a surface worth a second machine opinion, or for a full pre-release sweep.
- Network access is needed for `--config auto`; if offline, use `--config p/python`.

## ruff security rules

Ruff is already the repos' linter. Its `S` (flake8-bandit) and `ASYNC` rules overlap bandit cheaply:

```bash
uvx ruff check --select S,ASYNC,B .
```

- `S` = bandit rules, `ASYNC` = blocking calls in async paths (a DoS and correctness surface in these async services), `B` = bugbear (mutable defaults, etc.).
- Respect the repo's existing ruff config; report only security-relevant hits, not style.

## Reading the output together

1. Collect every hit with file:line.
2. For each, open the code and decide: real (confirm the failure path) or false positive (one-line reason).
3. Map each real hit to a threat surface in `netigen-threat-surfaces.md`, or note it as a standalone finding.
4. Carry the confirmed set into the report. Dropped hits are not listed, but keep a short note of how many and why, so the report shows the sweep was real.
