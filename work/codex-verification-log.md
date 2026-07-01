# Codex Verification Log

> Use this template to record evidence for local project tasks. Add newest entries at the top.

## Template

### YYYY-MM-DD Task Name

| Field | Notes |
|---|---|
| Expected Observation | What should be true after the command, edit, test, screenshot, or inspection? |
| Actual Result | What actually happened? Include concise output or artifact paths. |
| Deviation / Surprise | What differed from expectation? If none, write `None`. |
| Verification Command | Command, test, screenshot path, or file check used. |
| Residual Risk | What remains uncertain or unverified? |

## Entries

### 2026-07-01 Project File and Document Cleanup

| Field | Notes |
|---|---|
| Expected Observation | Outdated entry docs are updated, ignored temporary artifacts are removed, authoritative protocol references point to `UDP字段冻结_v1.2.md`, and Python tests still pass. |
| Actual Result | Updated AGENTS, CLAUDE, README, current board, development plan, UDP docs, TD bridge comment, cleanup record, data README, and blackboard. Removed caches, old zip backups, mock CSV, duplicate reference zip, and garbled Unity/MCP runtime mirror. Python 3.14.4 tests passed: 42 passed. |
| Deviation / Surprise | The previous `.hermes-venv` interpreter no longer exists; `py -3.14` is the current valid Python entry. |
| Verification Command | `py -3.14 -m pytest '02-技术研发/01-数据采集/tests' '02-技术研发/02-信号处理/tests' '02-技术研发/05-通信协议/tests' '02-技术研发/tests' -q`; `rg` consistency scans; `git diff --check`; targeted `Test-Path` checks for removed artifacts. |
| Residual Risk | Unity generated cache directories remain intentionally preserved to avoid slow reimport; stage 6/7 evidence materials still need to be populated under `04-成果与交付/`. |

### 2026-06-24 Enable SAPIEN-Lite Workflow

| Field | Notes |
|---|---|
| Expected Observation | `AGENTS.md` contains an appended `Codex Workflow` section; `work/` contains blackboard, verification log, and evaluation harness templates. |
| Actual Result | All three workflow files exist; `AGENTS.md` contains `Codex Workflow`; templates contain the required blackboard, verification, and 30-task harness sections. |
| Deviation / Surprise | `git diff --stat` only showed tracked files before staging; untracked `work/` files are expected to appear in `git status`. |
| Verification Command | `Test-Path work/codex-blackboard.md`; `Test-Path work/codex-verification-log.md`; `Test-Path work/codex-evaluation-harness.md`; `rg -n "Codex Workflow|Current Task Goal|Expected Observation|30-Task Log|High-Risk Action Intercepted" AGENTS.md work` |
| Residual Risk | Workflow quality depends on future tasks consistently updating the blackboard and verification log. |
