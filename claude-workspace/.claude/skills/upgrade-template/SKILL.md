# /upgrade-template - Upgrade Template Version

## Usage

```bash
/upgrade-template                 # Upgrade to latest version
/upgrade-template 1.5.0           # Upgrade to specific version
/upgrade-template --check         # Check available updates (no changes)
/upgrade-template --dry-run       # Preview changes without applying
```

## Key Feature

Automatically pulls latest template from remote repository. No local CHANGELOG.md needed.

**Template Repository**: `https://bitbucket.vissoft.vn/scm/ct/template-ai-team.git`
**Tag Format**: `X.X.X-RELEASE` (e.g., `1.7.0-RELEASE`)

Override repo URL in `.template-version`:
```json
{ "templateRepository": "https://your-git-server.com/template-ai-team.git" }
```

## Automated Script

**Primary execution method** - use the JS script:
```bash
node .claude/skills/upgrade-template/upgrade-template.js [TARGET_VERSION] [--check|--dry-run]
```

The script automates: version check → pull template → compare files → backup → apply updates → run migrations → update version.

**Use manual steps below only if the script fails.**

## Prerequisites

- `.template-version` file (created by `/project-setup`):
```json
{
  "version": "1.4.0",
  "installed": "2026-01-28",
  "lastUpgrade": "2026-01-28",
  "previousVersion": "1.3.0",
  "customizations": {
    "skills": [],
    "agents": [],
    "config": []
  }
}
```

If missing, skill prompts for current version and creates the file.

---

## Manual Workflow Steps (Fallback)

### Step 1: Pull Template Repository
```bash
# Clone or update template
git clone https://bitbucket.vissoft.vn/scm/ct/template-ai-team.git .template-upgrade/template-repo/
# Or if exists:
cd .template-upgrade/template-repo/ && git fetch --all --tags && git pull origin master && cd ../..
```

### Step 2: Determine Versions
- Read current version from `.template-version`
- List available versions: `cd .template-upgrade/template-repo/ && git tag -l "*-RELEASE" | sort -V`
- Tags use format `X.X.X-RELEASE`

### Step 3: Checkout Target Version
```bash
cd .template-upgrade/template-repo/ && git checkout X.X.X-RELEASE
```

### Step 4: Analyze Changes
Read CHANGELOG from **template repo** (not local project) between current and target version.
Categorize: Skills, Agents, Docs, Scripts, Config, Templates.

### Step 5: Compare Files (Two-Way)
Compare each file: project version vs new template version.
Results: `SAFE_UPDATE` (user hasn't modified), `NEW_FILE`, or `CONFLICT` (user customized).

Customizable files to flag as conflicts (never auto-overwrite):
- `PROJECT.md`, `.env*`, `config/`, `.template-version`

### Step 6: Create Backup
```bash
mkdir -p .template-upgrade-backup/
# Backup .claude/, docs/, scripts/ and .template-version
```

**Note**: On Windows, use `fs.cpSync()` or `xcopy` instead of `cp -r`.

### Step 7: Apply Updates
- Copy safe files from template to project
- Add new files
- Preserve user-customized files, save template version as `.new` for manual review
- Generate conflict report: `.template-upgrade/CONFLICTS.md`

**Safe defaults**: Skills (keep existing + add new), Scripts (use template), Core docs (keep user version).

### Step 8: Run Migration Scripts

Migration scripts are searched in this order:
1. Template repo: `.template-upgrade/template-repo/scripts/migrations/`
2. Project fallback: `scripts/migrations/`

Two filename patterns tried (exact version first, then wildcard):
```bash
# Exact match
migrate-1.8.2-to-1.9.0.js
# Wildcard (any patch of major.minor)
migrate-1.8.x-to-1.9.0.js
```

Run manually if script fails:
```bash
# From template repo (preferred)
node .template-upgrade/template-repo/scripts/migrations/migrate-X.Y.x-to-Z.Z.Z.js
# Or from project
node scripts/migrations/migrate-X.X.X-to-Y.Y.Y.js
```

Only runs if a matching migration file is found.

### Step 9: Update `.template-version`
Set new version, update `lastUpgrade` date, record `previousVersion`.

---

## Post-Upgrade

1. Review conflicts: `cat .template-upgrade/CONFLICTS.md`
2. Test project: `/auto-build check && /auto-build test`
3. Commit: `git commit -m "chore: upgrade template from X.X.X to Y.Y.Y"`
4. Clean up (after confirming everything works): `rm -rf .template-upgrade/ .template-upgrade-backup/`

## Rollback

Restore ALL backed-up directories (not just `.claude/`):
```bash
# Restore everything from backup
cp -r .template-upgrade-backup/backup-TIMESTAMP/* .
# Or restore specific dirs:
cp -r .template-upgrade-backup/backup-TIMESTAMP/.claude/ .claude/
cp -r .template-upgrade-backup/backup-TIMESTAMP/docs/ docs/
cp -r .template-upgrade-backup/backup-TIMESTAMP/scripts/ scripts/
# Restore version file
git checkout .template-version
```

## Known Limitations

1. **Two-way comparison**: Current implementation compares project vs new template. Does NOT do three-way comparison with old template version — can't detect "both sides changed" precisely.
2. **Private repos**: If `git clone` fails with auth error, configure Git credentials for the template repository first.
3. **No tags**: If target version tag doesn't exist, the script falls back to latest master. Verify tags with `git tag -l "*-RELEASE"` in `.template-upgrade/template-repo/`.
4. **Hardcoded template URL**: The JS uses `TEMPLATE_REPO` constant. To override for a fork, edit the constant directly in `upgrade-template.js`.

## Error Handling

| Error | Solution |
|-------|----------|
| Cannot determine version | Create `.template-version` manually |
| Conflicts detected | Review `.template-upgrade/CONFLICTS.md`, merge manually |
| Migration script failed | Run manually: `node scripts/migrations/migrate-X-to-Y.js` |
| Git clone auth failed | Configure Git credentials for template repo |
| Tag not found | Verify tag exists: `git tag -l "X.X.X-RELEASE"` in template repo |
| Backup directory full | Clean old backups: `rm -rf .template-upgrade-backup/` |

## Workspace Repo Support

Works correctly for workspace repos (Path C setup — `.claude/`, `docs/`, `scripts/` only, no source code).

- `PROJECT.md` is always flagged as CONFLICT → user reviews manually, `source-repos` section preserved
- `docs/tasks/` task content is untouched (not present in template)
- Missing source code dirs (no `src/`, `pom.xml`, etc.) are skipped gracefully

## Related Skills

- `/project-setup` - Creates `.template-version` during initial setup
- `/release` - For template maintainers releasing new versions (creates `X.X.X-RELEASE` tags)

---

**Skill Type**: Template Management
**Safety**: Automatic backups, rollback support, dry-run mode
