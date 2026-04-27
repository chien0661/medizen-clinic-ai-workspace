# Template Migration Scripts

This directory contains migration scripts for upgrading projects between template versions.

## Purpose

When the template introduces breaking changes or structural updates, migration scripts help projects upgrade smoothly by automatically converting old structures to new ones.

## How Migrations Work

1. **Triggered by `/upgrade-template` skill**
   - When upgrading from version X.X.X to Y.Y.Y
   - Skill checks for migration script: `migrate-X.X.X-to-Y.Y.Y.js`
   - Runs migration automatically during upgrade process

2. **Manual execution** (if needed)
   ```bash
   node scripts/migrations/migrate-1.4.0-to-1.5.0.js
   ```

## Migration Script Format

```javascript
#!/usr/bin/env node

/**
 * Migration: X.X.X → Y.Y.Y
 * Purpose: [Description of what this migration does]
 */

console.log('🔄 Migration: X.X.X → Y.Y.Y');

// 1. Check if migration needed
// 2. Backup important files
// 3. Apply changes
// 4. Verify success
// 5. Report status

console.log('✅ Migration complete');
```

## Available Migrations

### 1.4.0 → 1.5.0

**File**: `migrate-1.4.0-to-1.5.0.js`

**Purpose**: Convert single-file task tracking to multi-file system

**What it does**:
- Backs up `docs/tasks/dashboard.md`
- Runs `scripts/migrate-tasks-to-multifile.js`
- Converts tasks to individual files: `docs/tasks/TASK-XXX.md`
- Generates auto-updated dashboard: `docs/tasks/dashboard.md`

**When needed**: Projects using single-file `docs/tasks/dashboard.md` format

**Safe to run multiple times**: Yes (checks if already migrated)

## Creating New Migrations

When releasing a new template version with breaking changes:

1. **Create migration script**:
   ```bash
   touch scripts/migrations/migrate-X.X.X-to-Y.Y.Y.js
   chmod +x scripts/migrations/migrate-X.X.X-to-Y.Y.Y.js
   ```

2. **Implement migration logic**:
   - Check if migration is needed
   - Backup files before changing
   - Apply transformations
   - Validate results
   - Provide clear output

3. **Test thoroughly**:
   - Test on project with old version
   - Verify all data preserved
   - Ensure idempotent (safe to run multiple times)

4. **Document in CHANGELOG**:
   ```markdown
   ### Changed (Breaking)
   - [Description of breaking change]
   - **Migration**: Automatic migration runs during `/upgrade-template`
   - **Manual**: `node scripts/migrations/migrate-X.X.X-to-Y.Y.Y.js`
   ```

## Best Practices

1. **Always backup before migrating**
   ```javascript
   fs.copyFileSync('important-file.md', 'important-file.md.backup');
   ```

2. **Check if migration already ran**
   ```javascript
   if (alreadyMigrated()) {
     console.log('ℹ️  Already migrated, skipping');
     process.exit(0);
   }
   ```

3. **Provide clear output**
   - Show what's happening
   - Report success/failure clearly
   - Suggest next steps if manual action needed

4. **Make idempotent**
   - Safe to run multiple times
   - Detect if already migrated
   - Don't fail if target state already exists

5. **Handle errors gracefully**
   ```javascript
   try {
     // Migration logic
   } catch (error) {
     console.error('❌ Migration failed:', error.message);
     console.error('   Manual steps: ...');
     process.exit(1);
   }
   ```

## Testing Migrations

1. **Create test project with old version**
   ```bash
   # Setup project with version X.X.X
   cd test-project
   # Manually set to old version
   ```

2. **Run migration**
   ```bash
   node scripts/migrations/migrate-X.X.X-to-Y.Y.Y.js
   ```

3. **Verify results**
   - Check files converted correctly
   - Verify data integrity
   - Test that project still works

4. **Test idempotence**
   ```bash
   # Run again - should skip gracefully
   node scripts/migrations/migrate-X.X.X-to-Y.Y.Y.js
   ```

## Troubleshooting

### Migration fails partway through

**Solution**: Restore from backup
```bash
cp important-file.md.backup important-file.md
```

### Migration detects wrong state

**Solution**: Manually verify state, fix if needed
```bash
# Check what migration expects vs actual state
ls -la docs/tasks/
```

### Need to force re-migration

**Solution**: Delete migration marker/target
```bash
# Remove migrated files
rm -rf docs/tasks/*.md
# Re-run migration
node scripts/migrations/migrate-X.X.X-to-Y.Y.Y.js
```

---

**Last Updated**: 2026-02-03
**For**: Template versions 1.5.0+
