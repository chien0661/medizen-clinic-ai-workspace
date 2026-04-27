# Parallel Track Orchestration

Run **5 Claude Code dev agents in parallel**, each owning a slice of the 25-task roadmap.

---

## Why 5 tracks?

Critical path analysis (see `docs/tasks/dashboard.md`) shows 5 dev agents = sweet spot of cost vs. throughput. Going to 7+ only shaves ~2-3 weeks because the chain `001 -> 002 -> 003 -> 004 -> 005 -> 007 -> 013 -> 015 -> 025` is irreducibly sequential.

| Track | Title              | Queue (ordered)                                              | Theme                                        |
|-------|--------------------|--------------------------------------------------------------|----------------------------------------------|
| BE-A  | Core Pipeline      | 001 -> 002 -> 003 -> 004 -> 005 -> 007 -> 009                 | Foundation, RLS, Auth, RBAC, Patient, Visit  |
| BE-B  | Inventory & Billing| 006 -> 012 -> 011 -> 013                                      | Settings, Inventory FEFO, Rx, Invoice        |
| BE-C  | Operations         | 008 -> 010 -> 014 -> 015                                      | Appointment, Services, HR, Reports/Jobs      |
| FE-1  | Clinical UI        | 016 -> 017 -> 018 -> 019 -> 024                               | Tauri, Shell, Reception, Doctor, Dashboard   |
| FE-2  | Support UI         | 020 -> 021 -> 022 -> 023                                      | Pharmacy, Billing, HR, Admin                 |

---

## Quick start

```powershell
# Launch all 5 tracks (opens 5 PowerShell windows, each running `claude`)
.\scripts\launch-parallel-devs.ps1

# Launch a subset
.\scripts\launch-parallel-devs.ps1 -Tracks "BE-A,FE-1"

# Preview without opening anything
.\scripts\launch-parallel-devs.ps1 -DryRun
```

Each window:
1. Sets its title to the track name (e.g. `BE-A | Core Pipeline`).
2. Starts `claude` with a track-scoped prompt that locks the agent to its queue.
3. Reads `docs/tasks/dashboard.md` and picks the first runnable task.
4. Runs the standard pipeline via the `manager` skill: Implementation -> Review -> Test -> Documentation.

---

## Monitor progress

From any terminal:

```bash
# One-shot full report
node scripts/check-track-status.js

# Just one track
node scripts/check-track-status.js --track BE-A

# Compact view: only the next runnable task per track
node scripts/check-track-status.js --next

# Live mode (refresh every 30s)
node scripts/check-track-status.js --watch
```

Output legend:
- **DONE** (green) — task complete
- **DOCUMENTING / IN_TESTING / IN_REVIEW / IN_PROGRESS** — actively in flight
- **TODO** (gray) — not started
- **-> next: ... READY** — agent should pick this up now
- **-> next: ... blocked by ...** — agent must wait

---

## How blocking works across tracks

Each task declares blockers in its frontmatter and they show up in `dashboard.md`. The track agent will:

1. Walk its queue from the top.
2. For each TODO task, check that **every blocker is DONE**.
3. If yes -> pick it up.
4. If no -> wait. Re-poll dashboard every ~10 min.

**Cross-track dependencies are common**:
- BE-B's TASK-006 waits on BE-A's TASK-004 + TASK-005.
- FE-1's TASK-017 waits on BE-A's TASK-003 (Auth contract).
- FE-2's TASK-020 waits on BE-B's TASK-011 + TASK-012.

This means **early on, only BE-A is moving**. Other tracks idle until their first dependency clears. That is by design — there is no way around the critical path.

**Soft unblock for FE**: FE module tasks may begin when their BE counterpart hits **IN_REVIEW** (API contract is stable enough to integrate against). The track prompt allows this; if you want strict DONE-only, edit `Build-Prompt` in the launcher.

---

## Operational guidelines

### Pause / resume a track
Close its PowerShell window. Relaunch with `-Tracks "BE-A"` to pick up where it left off (state lives in `docs/tasks/`, not in memory).

### Recover a crashed agent
1. Check `dashboard.md` — find any task stuck in IN_PROGRESS / IN_REVIEW for too long.
2. Run `/task-status TASK-XXX TODO` to reset, or let the original agent retry on next poll.
3. Re-launch the affected track only.

### Avoid double-booking
The script does not enforce mutual exclusion at the OS level — it relies on each agent obeying its track queue. **Do not manually start work on a task owned by another track** while parallel agents are running, or you will race them on file edits.

### Token budget
5 parallel `claude` sessions = ~5x token cost vs. sequential. Estimated per-track usage: 200K-500K tokens per task depending on complexity. Plan accordingly.

### When to scale down
Once you reach the integration phase (TASK-025), shut down all tracks. TASK-025 is single-threaded by definition — keeping 4 idle agents running just burns tokens.

```powershell
# Run only the integration agent
.\scripts\launch-parallel-devs.ps1 -Tracks "BE-A"
# (then have it pick up TASK-025 manually)
```

---

## Files

| File                                          | Purpose                                       |
|-----------------------------------------------|-----------------------------------------------|
| `scripts/launch-parallel-devs.ps1`            | PowerShell launcher (spawns 5 windows)        |
| `scripts/check-track-status.js`               | Status reporter (one-shot or `--watch`)       |
| `docs/tasks/dashboard.md`                     | Source of truth for task status & blockers    |
| `docs/guide/workflow/MULTI_AGENT_ORCHESTRATION.md` | The single-feature pipeline each agent runs   |

---

## Troubleshooting

**"PowerShell windows close immediately"** — script uses `-NoExit`. If they still close, a PowerShell ExecutionPolicy is blocking. Run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

**"Agent picks the wrong task"** — check the track prompt in `Build-Prompt`. The agent only sees its queue; if it is grabbing tasks outside that list, the prompt was not loaded correctly. Verify by typing `/help` in the window — should show the standard skill list, then re-paste the track prompt.

**"`node` not found in spawned window"** — the new PowerShell inherits PATH from the parent. Confirm `node --version` works in your parent shell first.

**"Two agents touched the same file"** — should not happen if each obeys its queue, but if it does, the second commit will conflict. Resolve manually, then audit the agent prompt for queue leakage.
