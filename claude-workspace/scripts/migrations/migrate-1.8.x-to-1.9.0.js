#!/usr/bin/env node

/**
 * Migration: 1.8.x → 1.9.0
 * Purpose: Restructure docs/ folder — per-task folders, guide/ reorganization
 *
 * Changes handled:
 *   1. docs/tasks/TASK-XXX.md   → docs/tasks/TASK-XXX/task.md  (+ create subdirs)
 *   2. docs/tasks.md            → docs/tasks/dashboard.md       (dashboard move)
 *   3. docs/handoffs/TASK-*.*   → docs/tasks/TASK-XXX/handoff/
 *   4. docs/reviews/TASK-*.*    → docs/tasks/TASK-XXX/handoff/review-report.md
 *   5. docs/test-reports/TASK-* → docs/tasks/TASK-XXX/deliveries/test-reports/
 *   6. docs/bugs/BUG-*.*        → docs/tasks/TASK-XXX/bugs/  (via parent_task parse)
 *   7. docs/tasks/TASK-XXX-NN.* → warn about orphaned subtask files
 *   8. docs/specs/              → docs/templates/specs/
 *   9. guide files at docs/ root → docs/guide/{workflow,setup,reference}/
 *  10. .gitignore               → add task bugs/ to gitignore
 */

const fs = require('fs');
const path = require('path');

// ─── Helpers ────────────────────────────────────────────────────────────────

let warnings = [];
let migrated = [];
let skipped = [];

function log(msg) { console.log(msg); }
function warn(msg) { console.warn(`  ⚠️  ${msg}`); warnings.push(msg); }
function ok(msg)   { console.log(`  ✅ ${msg}`); migrated.push(msg); }
function skip(msg) { console.log(`  ⏭️  ${msg}`); skipped.push(msg); }

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function moveFile(src, dest) {
  ensureDir(path.dirname(dest));
  fs.renameSync(src, dest);
}

function copyFile(src, dest) {
  ensureDir(path.dirname(dest));
  fs.copyFileSync(src, dest);
}

/** Extract task ID (any PREFIX-NNN format) from a filename.
 *  Handles: TASK-001, BUG-001, UC-183, US-42, FEAT-10, etc.
 */
function extractTaskId(filename) {
  const m = filename.match(/^([A-Z][A-Z0-9]*-\d+)/i);
  return m ? m[0].toUpperCase() : null;
}

/** Check if ID is a subtask (PREFIX-NNN-NN — trailing 2-digit segment) */
function isSubtaskId(id) {
  return /^[A-Z][A-Z0-9]*-\d+-\d{2}$/i.test(id);
}

/** Parse parent_task from bug file content.
 *  Supports any task ID format (PREFIX-NNN):
 *   - YAML frontmatter: `parent_task: TASK-001` or `parent_task: UC-183`
 *   - Markdown field:   `**Feature:** TASK-001 - ...`
 */
function parseBugParentTask(content) {
  // YAML frontmatter
  const yamlMatch = content.match(/^---[\s\S]*?parent_task:\s*([A-Z][A-Z0-9]*-\d+)[\s\S]*?---/m);
  if (yamlMatch) return yamlMatch[1].toUpperCase();

  // Markdown **Feature:** line
  const mdMatch = content.match(/\*\*Feature:\*\*\s*([A-Z][A-Z0-9]*-\d+)/i);
  if (mdMatch) return mdMatch[1].toUpperCase();

  return null;
}

// ─── Check: already migrated? ───────────────────────────────────────────────

log('');
log('═══════════════════════════════════════════════════');
log('Migration: 1.8.x → 1.9.0');
log('docs/ restructure — per-task folders');
log('═══════════════════════════════════════════════════');
log('');

// If no tasks directory at all, skip everything
if (!fs.existsSync('docs/tasks')) {
  log('ℹ️  No docs/tasks/ found — new project setup, skipping migration');
  process.exit(0);
}

// ─── Step 1: Convert docs/tasks/TASK-XXX.md → docs/tasks/TASK-XXX/task.md ──

log('Step 1: Convert task files to task folders');

const TASK_SUBDIRS = [
  'specs',
  'handoff',
  'bugs',
  path.join('deliveries', 'test-cases'),
  path.join('deliveries', 'test-reports'),
  path.join('deliveries', 'api-specs'),
  path.join('deliveries', 'sql-scripts'),
  path.join('deliveries', 'final-specs'),
];

const taskEntries = fs.readdirSync('docs/tasks', { withFileTypes: true });

for (const entry of taskEntries) {
  if (!entry.isFile()) continue;
  if (!entry.name.endsWith('.md')) continue;
  if (entry.name === 'dashboard.md') continue;
  if (entry.name.endsWith('.backup') || entry.name.endsWith('.pre-migration')) continue;

  const baseName = entry.name.replace(/\.md$/, '');

  // Detect subtask IDs (TASK-XXX-NN)
  if (isSubtaskId(baseName)) {
    const parentId = baseName.replace(/-\d{2}$/, '');
    warn(`Subtask file detected: docs/tasks/${entry.name}`);
    warn(`  → Subtask support removed in v1.9.0. Move content to parent task's specs/ folder.`);
    warn(`  → Parent: docs/tasks/${parentId}/specs/`);
    continue;
  }

  const taskId = extractTaskId(baseName);
  if (!taskId) {
    skip(`Unknown file format, skipping: docs/tasks/${entry.name}`);
    continue;
  }

  const taskDir = path.join('docs/tasks', taskId);
  const destTaskFile = path.join(taskDir, 'task.md');

  if (fs.existsSync(destTaskFile)) {
    skip(`Already migrated: ${taskId}`);
    continue;
  }

  // Create task folder + subdirs
  ensureDir(taskDir);
  for (const sub of TASK_SUBDIRS) {
    ensureDir(path.join(taskDir, sub));
  }

  // Move task file
  moveFile(path.join('docs/tasks', entry.name), destTaskFile);
  ok(`${taskId}: docs/tasks/${entry.name} → docs/tasks/${taskId}/task.md`);
}

log('');

// ─── Step 2: Move docs/tasks.md → docs/tasks/dashboard.md ──────────────────

log('Step 2: Move dashboard file');

if (fs.existsSync('docs/tasks.md')) {
  const dest = 'docs/tasks/dashboard.md';
  if (fs.existsSync(dest)) {
    skip('docs/tasks/dashboard.md already exists — not overwriting');
  } else {
    moveFile('docs/tasks.md', dest);
    ok('docs/tasks.md → docs/tasks/dashboard.md');
  }
} else {
  skip('docs/tasks.md not found (already renamed or new project)');
}

log('');

// ─── Step 3: Migrate docs/handoffs/ ─────────────────────────────────────────

log('Step 3: Migrate docs/handoffs/ → per-task handoff/');

if (fs.existsSync('docs/handoffs')) {
  const handoffFiles = fs.readdirSync('docs/handoffs').filter(f => !f.startsWith('.'));

  for (const file of handoffFiles) {
    const taskId = extractTaskId(file);
    if (!taskId) {
      warn(`Cannot determine task ID for docs/handoffs/${file} — skipping`);
      continue;
    }

    const taskDir = path.join('docs/tasks', taskId);
    if (!fs.existsSync(taskDir)) {
      warn(`Task folder not found for ${file} (expected: ${taskDir}) — skipping`);
      continue;
    }

    const src = path.join('docs/handoffs', file);
    const dest = path.join(taskDir, 'handoff', file);

    if (fs.existsSync(dest)) {
      skip(`Already exists: ${dest}`);
      continue;
    }

    moveFile(src, dest);
    ok(`handoffs/${file} → tasks/${taskId}/handoff/${file}`);
  }

  // Remove empty handoffs dir
  const remaining = fs.readdirSync('docs/handoffs').filter(f => !f.startsWith('.'));
  if (remaining.length === 0) {
    fs.rmdirSync('docs/handoffs');
    ok('Removed empty docs/handoffs/');
  }
} else {
  skip('docs/handoffs/ not found');
}

log('');

// ─── Step 4: Migrate docs/reviews/ ──────────────────────────────────────────

log('Step 4: Migrate docs/reviews/ → per-task handoff/review-report.md');

if (fs.existsSync('docs/reviews')) {
  const reviewFiles = fs.readdirSync('docs/reviews').filter(f => !f.startsWith('.'));

  for (const file of reviewFiles) {
    const taskId = extractTaskId(file);
    if (!taskId) {
      warn(`Cannot determine task ID for docs/reviews/${file} — skipping`);
      continue;
    }

    const taskDir = path.join('docs/tasks', taskId);
    if (!fs.existsSync(taskDir)) {
      warn(`Task folder not found for ${file} (expected: ${taskDir}) — skipping`);
      continue;
    }

    const src = path.join('docs/reviews', file);
    // Rename to review-report.md (new convention) if it's the main review file
    const destName = file.endsWith('-review.md') ? 'review-report.md' : file;
    const dest = path.join(taskDir, 'handoff', destName);

    if (fs.existsSync(dest)) {
      skip(`Already exists: ${dest}`);
      continue;
    }

    moveFile(src, dest);
    ok(`reviews/${file} → tasks/${taskId}/handoff/${destName}`);
  }

  // Remove empty reviews dir
  const remaining = fs.readdirSync('docs/reviews').filter(f => !f.startsWith('.'));
  if (remaining.length === 0) {
    fs.rmdirSync('docs/reviews');
    ok('Removed empty docs/reviews/');
  }
} else {
  skip('docs/reviews/ not found');
}

log('');

// ─── Step 5: Migrate docs/test-reports/ ─────────────────────────────────────

log('Step 5: Migrate docs/test-reports/ → per-task deliveries/test-reports/');

if (fs.existsSync('docs/test-reports')) {
  const testReportFiles = fs.readdirSync('docs/test-reports').filter(f => !f.startsWith('.') && f !== '.gitkeep');

  for (const file of testReportFiles) {
    const taskId = extractTaskId(file);
    if (!taskId) {
      warn(`Cannot determine task ID for docs/test-reports/${file} — skipping`);
      continue;
    }

    const taskDir = path.join('docs/tasks', taskId);
    if (!fs.existsSync(taskDir)) {
      warn(`Task folder not found for ${file} (expected: ${taskDir}) — skipping`);
      continue;
    }

    const src = path.join('docs/test-reports', file);
    const dest = path.join(taskDir, 'deliveries', 'test-reports', file);

    if (fs.existsSync(dest)) {
      skip(`Already exists: ${dest}`);
      continue;
    }

    moveFile(src, dest);
    ok(`test-reports/${file} → tasks/${taskId}/deliveries/test-reports/${file}`);
  }

  // Remove empty test-reports dir
  const remaining = fs.readdirSync('docs/test-reports').filter(f => !f.startsWith('.') && f !== '.gitkeep');
  if (remaining.length === 0) {
    try { fs.rmSync('docs/test-reports', { recursive: true }); } catch (_) {}
    ok('Removed empty docs/test-reports/');
  }
} else {
  skip('docs/test-reports/ not found');
}

log('');

// ─── Step 6: Migrate docs/bugs/ ─────────────────────────────────────────────

log('Step 6: Migrate docs/bugs/ → per-task bugs/ (via parent_task)');

if (fs.existsSync('docs/bugs')) {
  const bugFiles = fs.readdirSync('docs/bugs').filter(f => !f.startsWith('.') && f !== '.gitkeep');

  for (const file of bugFiles) {
    const src = path.join('docs/bugs', file);
    const content = fs.readFileSync(src, 'utf-8');

    const parentTask = parseBugParentTask(content);
    if (!parentTask) {
      warn(`docs/bugs/${file}: no parent_task found — skipping (move manually)`);
      continue;
    }

    const taskDir = path.join('docs/tasks', parentTask);
    if (!fs.existsSync(taskDir)) {
      warn(`docs/bugs/${file}: parent task folder ${taskDir} not found — skipping`);
      continue;
    }

    const dest = path.join(taskDir, 'bugs', file);
    if (fs.existsSync(dest)) {
      skip(`Already exists: ${dest}`);
      continue;
    }

    moveFile(src, dest);
    ok(`bugs/${file} → tasks/${parentTask}/bugs/${file}`);
  }

  // Remove empty bugs dir
  const remaining = fs.readdirSync('docs/bugs').filter(f => !f.startsWith('.') && f !== '.gitkeep');
  if (remaining.length === 0) {
    try { fs.rmSync('docs/bugs', { recursive: true }); } catch (_) {}
    ok('Removed empty docs/bugs/');
  } else {
    warn(`${remaining.length} bug file(s) could not be assigned to a task — left in docs/bugs/`);
  }
} else {
  skip('docs/bugs/ not found');
}

log('');

// ─── Step 7: Move docs/specs/ → docs/templates/specs/ ───────────────────────

log('Step 7: Move docs/specs/ → docs/templates/specs/');

if (fs.existsSync('docs/specs')) {
  ensureDir('docs/templates/specs');
  const specFiles = fs.readdirSync('docs/specs').filter(f => !f.startsWith('.'));

  for (const file of specFiles) {
    const src = path.join('docs/specs', file);
    const dest = path.join('docs/templates/specs', file);

    if (fs.existsSync(dest)) {
      skip(`Already exists: docs/templates/specs/${file}`);
      continue;
    }

    if (fs.statSync(src).isDirectory()) {
      skip(`Skipping subdirectory: docs/specs/${file}`);
      continue;
    }

    moveFile(src, dest);
    ok(`specs/${file} → templates/specs/${file}`);
  }

  // Remove empty specs dir
  const remaining = fs.readdirSync('docs/specs').filter(f => !f.startsWith('.'));
  if (remaining.length === 0) {
    fs.rmdirSync('docs/specs');
    ok('Removed empty docs/specs/');
  }
} else {
  skip('docs/specs/ not found');
}

log('');

// ─── Step 8: Reorganize guide files into docs/guide/ ────────────────────────

log('Step 8: Reorganize guide files → docs/guide/');

const GUIDE_MAP = {
  'workflow': [
    'WORKFLOW.md',
    'MULTI_AGENT_ORCHESTRATION.md',
    'CONTRIBUTING.md',
  ],
  'setup': [
    'MCP_SETUP.md',
    'MCP_SETUP_PARTNER.md',
    'MCP_SETUP_VISSOFT.md',
    'MCP_MARIADB_SETUP.md',
    'TELEGRAM_NOTIFICATION_SETUP.md',
    'PLATFORM_COMPATIBILITY.md',
    'REMOTE_DEPLOYMENT_UPGRADE.md',
  ],
  'reference': [
    'SKILL_INVENTORY.md',
    'SLASH_COMMANDS_GUIDE.md',
    'AGENT_MANAGER_GUIDE.md',
    'PERSISTENT_MEMORY_ARCHITECTURE.md',
    'PUBLISHING_QUICK_REFERENCE.md',
    'VDS_CONFLUENCE_PUBLISHING.md',
    'RELEASE_PROCESS.md',
    'RELEASE_REPORT_EXAMPLE.md',
    'TELEGRAM_NOTIFICATION_REVIEW_PROCESS.md',
  ],
};

// Also check docs/guides/ subdirectory (old location for some files)
const GUIDES_SUBDIR_MAP = {
  'setup': [
    'remote-memory-deployment.md',
    'multi-team-deployment.md',
    'collaborative-memory.md',
    'UPGRADE-TO-PERSISTENT-MEMORY.md',
  ],
  'reference': [
    'using-persistent-memory.md',
  ],
};

if (fs.existsSync('docs/guide')) {
  skip('docs/guide/ already exists — skipping guide reorganization');
} else {
  for (const [subfolder, files] of Object.entries(GUIDE_MAP)) {
    ensureDir(path.join('docs/guide', subfolder));
    for (const file of files) {
      const src = path.join('docs', file);
      if (!fs.existsSync(src)) continue;
      const dest = path.join('docs/guide', subfolder, file);
      moveFile(src, dest);
      ok(`docs/${file} → docs/guide/${subfolder}/${file}`);
    }
  }

  // Files from old docs/guides/ subdirectory
  if (fs.existsSync('docs/guides')) {
    for (const [subfolder, files] of Object.entries(GUIDES_SUBDIR_MAP)) {
      for (const file of files) {
        const src = path.join('docs/guides', file);
        if (!fs.existsSync(src)) continue;
        const dest = path.join('docs/guide', subfolder, file);
        moveFile(src, dest);
        ok(`docs/guides/${file} → docs/guide/${subfolder}/${file}`);
      }
    }

    // Remove empty docs/guides/
    const remaining = fs.readdirSync('docs/guides').filter(f => !f.startsWith('.'));
    if (remaining.length === 0) {
      fs.rmdirSync('docs/guides');
      ok('Removed empty docs/guides/');
    }
  }
}

log('');

// ─── Step 9: Clean up stale .gitignore entries ───────────────────────────────

log('Step 9: Clean up stale .gitignore entries');

const GITIGNORE_PATH = '.gitignore';

// These entries were mistakenly added in earlier template versions.
// Task artifacts (handoffs, bugs, test-reports, test-cases) are collaborative
// team documents and must be committed to the repo.
const STALE_ENTRIES = [
  'docs/tasks/*/handoff/',
  'docs/tasks/*/bugs/',
  'docs/tasks/*/deliveries/test-reports/',
  'docs/tasks/*/deliveries/test-cases/',
];

if (fs.existsSync(GITIGNORE_PATH)) {
  let content = fs.readFileSync(GITIGNORE_PATH, 'utf-8');
  let changed = false;

  for (const entry of STALE_ENTRIES) {
    if (content.includes(entry)) {
      // Remove the line (and any preceding comment line about it)
      content = content
        .split('\n')
        .filter(line => !line.trim().startsWith(entry) && !line.includes(`# ${entry}`))
        .join('\n');
      changed = true;
      ok(`.gitignore: removed stale entry "${entry}"`);
    }
  }

  // Also remove the section header if left behind
  content = content.replace(/# Generated task artifacts.*?\n/g, '');
  content = content.replace(/# Handoffs and reviews are agent-internal.*?\n/g, '');
  content = content.replace(/# Bug reports are intermediate process.*?\n/g, '');
  content = content.replace(/# Test deliveries are generated.*?\n/g, '');

  if (changed) {
    fs.writeFileSync(GITIGNORE_PATH, content, 'utf-8');
  } else {
    skip('.gitignore: no stale task artifact entries found');
  }
} else {
  skip('.gitignore not found');
}

log('');

// ─── Summary ─────────────────────────────────────────────────────────────────

log('═══════════════════════════════════════════════════');
log('Migration Summary');
log('═══════════════════════════════════════════════════');
log(`  ✅ Migrated:  ${migrated.length} items`);
log(`  ⏭️  Skipped:   ${skipped.length} items`);
log(`  ⚠️  Warnings:  ${warnings.length} items`);
log('');

if (warnings.length > 0) {
  log('⚠️  Items requiring manual attention:');
  for (const w of warnings) {
    log(`   - ${w}`);
  }
  log('');
}

log('Next steps:');
log('  1. Review warnings above (if any)');
log('  2. Update cross-references in CLAUDE.md, README.md, PROJECT.md');
log('  3. Commit: git add -A && git commit -m "chore: migrate template to v1.9.0"');
log('');
log('✅ Migration complete');
log('');
