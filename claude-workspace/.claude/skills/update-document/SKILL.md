# /update-document - Documentation Update Command

## Usage

```bash
/update-document TASK-001                          # Update all documentation for task
/update-document TASK-001 --api-only               # Only update API documentation
/update-document TASK-001 --feature-only           # Only update feature documentation
/update-document TASK-001 --functional-design      # Generate/update functional design doc only
/update-document --all                             # Update docs for all DOCUMENTING tasks
/update-document --all --functional-design         # Generate functional design for all DONE tasks
```

## Retroactive Functional Design Generation

The `--functional-design` flag can be used on **any task** regardless of status (including DONE tasks).
This allows generating the functional design document for tasks that were completed before this template existed.

**What it does:**
1. Reads task details from `docs/tasks/TASK-ID/`
2. Reads existing deliveries: api-specs, test-reports, handoff notes, specs
3. Generates `docs/tasks/TASK-ID/deliveries/final-specs/[feature-name]-functional-design.md`
   using template `docs/templates/specs/functional-design-template.md`
4. Commits the new file
5. Does **NOT** change task status (preserves DONE status)

## What This Command Does

Spawns the **Documentation Agent** (`.claude/agents/documentation.md`) in isolated context.

### Workflow

```
[1] Validate task exists
    ├─ If --functional-design: accept any status (including DONE)
    └─ Otherwise: must be DOCUMENTING
[2] Spawn Documentation Agent
    ├─ Read task details, test report, review report, git diff
    ├─ Update API documentation (docs/tasks/TASK-ID/deliveries/api-specs/)
    ├─ Generate functional design document (docs/tasks/TASK-ID/deliveries/final-specs/)
    │   └─ Uses template: docs/templates/specs/functional-design-template.md
    ├─ Update architecture docs (docs/architecture/)
    ├─ Update configuration docs (docs/configuration.md)
    ├─ Update troubleshooting guide (docs/troubleshooting/)
    ├─ Commit documentation changes
    └─ Update task status: DOCUMENTING → DONE (skipped if --functional-design on DONE task)
[3] Validation: docs updated, examples working, no broken links
[END] Task marked DONE (or unchanged if retroactive --functional-design)
```

### Status Transitions

| Flag | Before | After Success | After Failure |
|------|--------|---------------|---------------|
| (none) | DOCUMENTING | DONE | DOCUMENTING (with error notes) |
| (none) | Other statuses | Error | Must be DOCUMENTING first |
| `--functional-design` | Any (incl. DONE) | Unchanged | Error noted |

## Model: `haiku`

When spawning the Documentation Agent via Task tool, pass `model: "haiku"`. Override via PROJECT.md `agent-models` section.

## Agent Documentation Steps

1. **Review All Artifacts** - Task requirements, code changes (git diff), review report, test report, API specs

2. **Update API Documentation** (`docs/tasks/TASK-ID/deliveries/api-specs/{endpoint-name}.md`)
   - Endpoints with request/response examples
   - Authentication requirements
   - Error codes and messages

3. **Generate Functional Design Document** (`docs/tasks/TASK-ID/deliveries/final-specs/{feature-name}-functional-design.md`)
   - Use template: `docs/templates/specs/functional-design-template.md`
   - Write in Vietnamese, natural language (no code blocks, SQL is OK)
   - Describe: feature overview, data flow, API behavior, DB schema, business rules, error handling, cache strategy
   - **For data aggregation / reporting tasks**: populate Section 7 with full SQL:
     - 7.1: UPSERT/INSERT scripts (consumer, ETL, batch jobs)
     - 7.2: Full SELECT queries per API/report — include all WHERE conditions, UNION branches, example values
     - 7.3: Parameter resolution logic (date ranges, granularity mapping) — describe in tables, not code
   - Target audience: testers and clients (not developers)

4. **Update Architecture Documentation** (`docs/architecture/`)
   - New components, layers, dependencies
   - Key methods and responsibilities

5. **Update Configuration Documentation** (`docs/configuration.md`)
   - New environment variables
   - Config examples

6. **Update Troubleshooting Guide** (`docs/troubleshooting/`)
   - Common issues with symptoms, causes, solutions

7. **Update README** (if major feature)

8. **Commit Documentation Changes**
   ```
   docs: add {feature} functional design and documentation
   Refs: TASK-XXX
   ```

9. **Update Task Status** → DONE with completion timestamp
   *(Skip if running with `--functional-design` on an already DONE task)*

10. **Create Completion Summary** (`docs/tasks/TASK-XXX/handoff/completion-summary.md`)
    - Implementation summary, quality metrics, deliverables, next steps

## Documentation Standards

- **API docs**: All endpoints, JSON examples, error codes, multi-language code examples, auth requirements
- **Feature docs**: Overview → how-to → tips → troubleshooting
- **Code examples**: Realistic (not "foo/bar"), success + error cases, with imports and comments
- **Architecture docs**: Layer, dependencies, responsibilities, key methods

## Quality Criteria

- API docs updated in `docs/tasks/TASK-ID/deliveries/api-specs/` (if API changes)
- **Functional design document generated** in `docs/tasks/TASK-ID/deliveries/final-specs/` (required for every task)
- Configuration docs updated (if new config)
- Troubleshooting guide updated (if new issues possible)
- Architecture docs updated (if new components)
- Functional design uses natural language — no code blocks, SQL is OK
- No broken internal links
- Proper markdown formatting

## Error Handling

| Error | Solution |
|-------|----------|
| Task not DOCUMENTING | Run `/test-task` first to ensure all tests pass |
| Missing artifacts | Agent creates docs from available artifacts, notes gaps |
| Documentation exists | Agent updates relevant sections, preserves manual content |

## Related Commands

- `/test-task` - Previous step (must pass before documentation)
- `/complete-task` - Full automation (includes documentation)
- `/confluence publish` - Publish documentation to Confluence
- `/jira export` - Sync completion status to Jira

---

**Skill Type**: Documentation (Agent Orchestration)
