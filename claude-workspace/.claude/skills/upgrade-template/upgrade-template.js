#!/usr/bin/env node

/**
 * Upgrade Template Skill
 *
 * Upgrades a project from one template version to another with intelligent merging
 *
 * Usage: node upgrade-template.js [TARGET_VERSION] [--check|--dry-run]
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const VERSION_FILE = '.template-version';
const CHANGELOG_FILE = 'CHANGELOG.md';
const BACKUP_DIR = '.template-upgrade-backup';
const UPGRADE_DIR = '.template-upgrade';
const TEMPLATE_CLONE_DIR = path.join(UPGRADE_DIR, 'template-repo');

const TEMPLATE_REPO = 'https://bitbucket.vissoft.vn/scm/ct/template-ai-team.git';

// Parse command line arguments
const args = process.argv.slice(2);
const targetVersion = args.find(arg => !arg.startsWith('--'));
const checkOnly = args.includes('--check');
const dryRun = args.includes('--dry-run');

console.log('');
console.log('========================================');
console.log('🔧 Template Upgrade Tool');
console.log('========================================');
console.log('');

/**
 * Main execution
 */
async function main() {
  try {
    // Step 1: Get current version
    const currentVersion = await getCurrentVersion();
    console.log(`📊 Current version: ${currentVersion}`);

    // Step 2: Pull template repo first (needed to determine latest version and analyze changes)
    console.log('📥 Fetching template repository...');
    const templatePath = await ensureTemplateRepo();
    console.log('');

    // Step 3: Get target version (latest from template repo, or specified by user)
    const target = targetVersion || getLatestVersionFromPath(templatePath);
    console.log(`🎯 Target version: ${target}`);
    console.log('');

    // Check only mode
    if (checkOnly) {
      return checkVersionStatus(currentVersion, target);
    }

    // Validate upgrade path
    if (compareVersions(currentVersion, target) >= 0) {
      console.log(`ℹ️  Already at version ${currentVersion}`);
      console.log('   No upgrade needed.');
      return;
    }

    console.log(`⬆️  Upgrade available: ${currentVersion} → ${target}`);
    console.log('');

    // Step 4: Analyze changes (reads from template repo's CHANGELOG)
    console.log('📋 Analyzing changes...');
    const changes = analyzeChanges(currentVersion, target, templatePath);
    displayChangeSummary(changes);
    console.log('');

    // Dry run mode
    if (dryRun) {
      console.log('🔍 Dry run mode - no changes will be made');
      console.log('');
      return displayDryRunResults(changes);
    }

    // Step 5: Detect conflicts
    console.log('🔍 Detecting conflicts...');
    const conflicts = await detectConflicts(changes);
    console.log('');

    if (conflicts.length > 0) {
      console.log(`⚠️  ${conflicts.length} conflict(s) detected:`);
      conflicts.forEach(c => console.log(`   - ${c.file}`));
      console.log('');
    }

    // Step 6: Create backup
    console.log('📦 Creating backup...');
    const backupPath = createBackup();
    console.log(`✅ Backup created: ${backupPath}`);
    console.log('');

    // Step 7: Apply updates (checkout specific tag, compare, copy)
    console.log('🚀 Applying updates...');
    await applyUpdates(changes, conflicts, target, templatePath);
    console.log('');

    // Step 8: Run migrations
    console.log('🔄 Running migrations...');
    await runMigrations(currentVersion, target, templatePath);
    console.log('');

    // Step 9: Update version
    console.log('📝 Updating version...');
    updateVersion(currentVersion, target);
    console.log('');

    // Success
    console.log('========================================');
    console.log(`✅ Upgrade complete: ${currentVersion} → ${target}`);
    console.log('========================================');
    console.log('');
    console.log('📝 Next steps:');
    console.log('   1. Review changes: git diff');
    console.log(`   2. Review conflicts: cat ${UPGRADE_DIR}/CONFLICTS.md`);
    console.log('   3. Test your project');
    console.log('   4. Commit: git add . && git commit -m "chore: upgrade template to ' + target + '"');
    console.log(`   5. If issues, restore backup: cp -r ${backupPath}/* .`);
    console.log('');

  } catch (error) {
    console.error('');
    console.error('❌ Error:', error.message);
    console.error('');
    process.exit(1);
  }
}

/**
 * Get current template version
 */
async function getCurrentVersion() {
  if (!fs.existsSync(VERSION_FILE)) {
    console.log('⚠️  No .template-version file found');
    console.log('');
    console.log('This project doesn\'t have version tracking enabled.');
    console.log('Please enter the template version this project was created with:');
    console.log('');
    console.log('Options:');
    console.log('1. 1.5.0 (latest)');
    console.log('2. 1.4.0');
    console.log('3. 1.3.2');
    console.log('4. Other (enter manually)');
    console.log('');

    // For now, default to 1.4.0 (will prompt in interactive mode)
    const version = '1.4.0';
    console.log(`Using default: ${version}`);
    console.log('');

    // Create version file
    initializeVersionFile(version);

    return version;
  }

  const versionData = JSON.parse(fs.readFileSync(VERSION_FILE, 'utf-8'));
  return versionData.version;
}

/**
 * Initialize version file
 */
function initializeVersionFile(version) {
  const versionData = {
    version: version,
    installed: new Date().toISOString().split('T')[0],
    lastUpgrade: new Date().toISOString().split('T')[0],
    customizations: {
      skills: [],
      agents: [],
      config: []
    }
  };

  fs.writeFileSync(VERSION_FILE, JSON.stringify(versionData, null, 2), 'utf-8');
  console.log(`✅ Version tracking initialized: ${VERSION_FILE}`);
  console.log('');
}

/**
 * Ensure template repository is cloned/updated (stays on default branch)
 * Returns the path to the cloned repo.
 */
async function ensureTemplateRepo() {
  if (!fs.existsSync(UPGRADE_DIR)) {
    fs.mkdirSync(UPGRADE_DIR, { recursive: true });
  }

  if (!fs.existsSync(TEMPLATE_CLONE_DIR)) {
    console.log('   Cloning template repository...');
    try {
      execSync(`git clone "${TEMPLATE_REPO}" "${TEMPLATE_CLONE_DIR}"`, { stdio: 'pipe' });
    } catch (error) {
      throw new Error(`Failed to clone template repository: ${error.message}`);
    }
  } else {
    console.log('   Updating template repository...');
    try {
      execSync('git fetch --all --tags', { cwd: TEMPLATE_CLONE_DIR, stdio: 'pipe' });
      // Return to default branch to read latest CHANGELOG
      execSync('git checkout master 2>/dev/null || git checkout main', { cwd: TEMPLATE_CLONE_DIR, stdio: 'pipe', shell: true });
      execSync('git pull', { cwd: TEMPLATE_CLONE_DIR, stdio: 'pipe' });
    } catch (error) {
      throw new Error(`Failed to update template repository: ${error.message}`);
    }
  }

  console.log('   ✅ Template repository ready');
  return TEMPLATE_CLONE_DIR;
}

/**
 * Get latest version from template repo's CHANGELOG
 */
function getLatestVersionFromPath(templatePath) {
  const changelogFile = path.join(templatePath, CHANGELOG_FILE);
  if (!fs.existsSync(changelogFile)) {
    throw new Error(`CHANGELOG.md not found in template repository at: ${changelogFile}`);
  }

  const changelog = fs.readFileSync(changelogFile, 'utf-8');
  const versionMatch = changelog.match(/^## \[(\d+\.\d+\.\d+)\]/m);

  if (!versionMatch) {
    throw new Error('Could not find latest version in template CHANGELOG.md');
  }

  return versionMatch[1];
}

/**
 * Compare versions (returns -1 if v1 < v2, 0 if equal, 1 if v1 > v2)
 */
function compareVersions(v1, v2) {
  const parts1 = v1.split('.').map(Number);
  const parts2 = v2.split('.').map(Number);

  for (let i = 0; i < 3; i++) {
    if (parts1[i] > parts2[i]) return 1;
    if (parts1[i] < parts2[i]) return -1;
  }

  return 0;
}

/**
 * Check version status (--check mode)
 */
function checkVersionStatus(current, latest) {
  console.log('========================================');
  console.log('📊 Template Version Status');
  console.log('========================================');
  console.log('');
  console.log(`Current Version: ${current}`);
  console.log(`Latest Version: ${latest}`);
  console.log('');

  if (compareVersions(current, latest) < 0) {
    console.log('Status: ⚠️  Update available');
    console.log('');
    console.log(`Run \`/upgrade-template\` to upgrade from ${current} to ${latest}`);
  } else {
    console.log('Status: ✅ Up to date');
  }

  console.log('');
}

/**
 * Analyze changes between versions (reads CHANGELOG from template repo)
 */
function analyzeChanges(fromVersion, toVersion, templatePath) {
  const changelogFile = path.join(templatePath, CHANGELOG_FILE);
  const changelog = fs.readFileSync(changelogFile, 'utf-8');

  // Extract versions between fromVersion and toVersion
  const fromIndex = changelog.indexOf(`## [${fromVersion}]`);
  const toIndex = changelog.indexOf(`## [${toVersion}]`);

  if (toIndex === -1) {
    throw new Error(`Could not find version ${toVersion} in CHANGELOG`);
  }

  // If fromVersion not found, take everything up to toVersion
  const relevantChangelog = fromIndex === -1
    ? changelog.substring(toIndex)
    : changelog.substring(toIndex, fromIndex);

  // Parse changes
  const changes = {
    skills: [],
    agents: [],
    docs: [],
    scripts: [],
    config: [],
    migrations: []
  };

  // Simple parsing (can be enhanced)
  const lines = relevantChangelog.split('\n');
  for (const line of lines) {
    if (line.includes('.claude/skills/')) {
      const match = line.match(/`.claude\/skills\/([^/`]+)/);
      if (match) changes.skills.push(match[1]);
    }
    if (line.includes('.claude/agents/')) {
      const match = line.match(/`.claude\/agents\/([^`]+)/);
      if (match) changes.agents.push(match[1]);
    }
    if (line.includes('CLAUDE.md') || line.includes('PROJECT.md')) {
      changes.docs.push('Core documentation');
    }
    if (line.includes('scripts/')) {
      const match = line.match(/`scripts\/([^`]+)/);
      if (match) changes.scripts.push(match[1]);
    }
  }

  // Remove duplicates
  changes.skills = [...new Set(changes.skills)];
  changes.agents = [...new Set(changes.agents)];
  changes.docs = [...new Set(changes.docs)];
  changes.scripts = [...new Set(changes.scripts)];

  return changes;
}

/**
 * Display change summary
 */
function displayChangeSummary(changes) {
  console.log('   Changes found:');

  if (changes.skills.length > 0) {
    console.log(`   ✅ ${changes.skills.length} skill(s): ${changes.skills.join(', ')}`);
  }

  if (changes.agents.length > 0) {
    console.log(`   ✅ ${changes.agents.length} agent(s): ${changes.agents.join(', ')}`);
  }

  if (changes.docs.length > 0) {
    console.log(`   ✅ ${changes.docs.length} documentation update(s)`);
  }

  if (changes.scripts.length > 0) {
    console.log(`   ✅ ${changes.scripts.length} script(s): ${changes.scripts.join(', ')}`);
  }
}

/**
 * Detect conflicts
 */
async function detectConflicts(changes) {
  const conflicts = [];

  // Check customized files
  // (This is a simplified version - real implementation would be more sophisticated)

  return conflicts;
}

/**
 * Create backup
 */
function createBackup() {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T').join('-').substring(0, 19);
  const backupPath = path.join(BACKUP_DIR, `backup-${timestamp}`);

  if (!fs.existsSync(BACKUP_DIR)) {
    fs.mkdirSync(BACKUP_DIR, { recursive: true });
  }

  // Backup critical directories
  const dirsToBackup = ['.claude', 'docs', 'scripts', 'mcp-servers'];

  fs.mkdirSync(backupPath, { recursive: true });

  for (const dir of dirsToBackup) {
    if (fs.existsSync(dir)) {
      execSync(`cp -r ${dir} ${backupPath}/`, { stdio: 'ignore' });
    }
  }

  // Backup version file
  if (fs.existsSync(VERSION_FILE)) {
    fs.copyFileSync(VERSION_FILE, path.join(backupPath, VERSION_FILE));
  }

  return backupPath;
}

/**
 * Checkout specific template version tag in the already-cloned repo
 */
function checkoutTemplateVersion(templatePath, targetVersion) {
  const tagName = `${targetVersion}-RELEASE`;

  console.log(`   📌 Checking out template version ${targetVersion}...`);
  try {
    execSync(`git checkout ${tagName}`, { cwd: templatePath, stdio: 'pipe' });
    console.log(`   ✅ Checked out tag: ${tagName}`);
  } catch (error) {
    // Try without -RELEASE suffix
    try {
      execSync(`git checkout v${targetVersion}`, { cwd: templatePath, stdio: 'pipe' });
      console.log(`   ✅ Checked out tag: v${targetVersion}`);
    } catch (e) {
      console.log(`   ⚠️  Tag ${tagName} not found, using latest master`);
    }
  }
}

/**
 * Compare project files with template version
 */
function compareWithTemplate(templatePath) {
  const comparisons = {
    safeToUpdate: [],
    conflicts: [],
    newFiles: [],
    unchanged: []
  };

  // Directories to compare
  const dirsToCompare = [
    { dir: '.claude/skills', type: 'skills' },
    { dir: '.claude/agents', type: 'agents' },
    { dir: 'docs', type: 'docs' },
    { dir: 'scripts', type: 'scripts' },
    { dir: 'mcp-servers', type: 'mcp-servers' }
  ];

  // Files to compare at root
  const filesToCompare = [
    'CLAUDE.md',
    'README.md',
    'CHANGELOG.md',
    '.gitignore',
    '.mcp.json.example',
    '.env.example'
  ];

  // Compare root files
  for (const file of filesToCompare) {
    const projectFile = file;
    const templateFile = path.join(templatePath, file);

    if (fs.existsSync(templateFile)) {
      if (fs.existsSync(projectFile)) {
        // File exists in both - check if different
        const projectContent = fs.readFileSync(projectFile, 'utf-8');
        const templateContent = fs.readFileSync(templateFile, 'utf-8');

        if (projectContent !== templateContent) {
          // Check if it's a customizable or core file that needs manual review
          if (isCustomizableFile(file) || file === 'CLAUDE.md' || file === 'README.md') {
            comparisons.conflicts.push({
              file: file,
              type: isCustomizableFile(file) ? 'modified-customizable' : 'modified-core',
              message: isCustomizableFile(file)
                ? 'File may have user customizations — review new template sections'
                : 'Core template file modified in project'
            });
          } else {
            comparisons.safeToUpdate.push({
              file: file,
              type: 'updated',
              source: templateFile
            });
          }
        } else {
          comparisons.unchanged.push(file);
        }
      } else {
        // New file in template
        comparisons.newFiles.push({
          file: file,
          type: 'new',
          source: templateFile
        });
      }
    }
  }

  // Compare directories
  for (const { dir, type } of dirsToCompare) {
    const templateDir = path.join(templatePath, dir);
    if (fs.existsSync(templateDir)) {
      compareDirectory(dir, templateDir, type, comparisons);
    }
  }

  return comparisons;
}

/**
 * Compare directory recursively
 */
function compareDirectory(projectDir, templateDir, type, comparisons) {
  if (!fs.existsSync(templateDir)) return;

  const templateFiles = getAllFiles(templateDir, templateDir);

  for (const relPath of templateFiles) {
    const templateFile = path.join(templateDir, relPath);
    const projectFile = path.join(projectDir, relPath);

    if (fs.existsSync(projectFile)) {
      // File exists in both
      const projectContent = fs.readFileSync(projectFile, 'utf-8');
      const templateContent = fs.readFileSync(templateFile, 'utf-8');

      if (projectContent !== templateContent) {
        // Check if it's a known customizable file
        if (isCustomizableFile(projectFile)) {
          comparisons.conflicts.push({
            file: projectFile,
            type: 'modified-customizable',
            message: 'File may have user customizations'
          });
        } else {
          comparisons.safeToUpdate.push({
            file: projectFile,
            type: 'updated',
            source: templateFile
          });
        }
      } else {
        comparisons.unchanged.push(projectFile);
      }
    } else {
      // New file in template
      comparisons.newFiles.push({
        file: projectFile,
        type: 'new',
        source: templateFile
      });
    }
  }
}

/**
 * Get all files in directory recursively
 */
function getAllFiles(dir, baseDir) {
  const files = [];

  function traverse(currentDir) {
    const entries = fs.readdirSync(currentDir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name);

      if (entry.isDirectory()) {
        // Skip certain directories
        if (entry.name !== '.git' && entry.name !== 'node_modules') {
          traverse(fullPath);
        }
      } else {
        const relPath = path.relative(baseDir, fullPath);
        files.push(relPath);
      }
    }
  }

  traverse(dir);
  return files;
}

/**
 * Check if file is customizable (should prompt user)
 */
function isCustomizableFile(filePath) {
  // Files that users typically customize
  // Note: .env.example and .mcp.json.example are templates, NOT customizable
  const customizablePatterns = [
    /PROJECT\.md$/,
    /\.env$/,
    /config\//,
    /\.template-version$/
  ];

  return customizablePatterns.some(pattern => pattern.test(filePath));
}

/**
 * Apply updates
 */
async function applyUpdates(changes, conflicts, targetVersion, templatePath) {
  let updateCount = 0;

  // Checkout specific version tag
  checkoutTemplateVersion(templatePath, targetVersion);
  console.log('');

  console.log('   🔍 Comparing files with template...');
  const comparisons = compareWithTemplate(templatePath);
  console.log('');

  // Display comparison summary
  console.log('   📊 Comparison Results:');
  console.log(`      Safe to update: ${comparisons.safeToUpdate.length} file(s)`);
  console.log(`      Conflicts (manual review): ${comparisons.conflicts.length} file(s)`);
  console.log(`      New files: ${comparisons.newFiles.length} file(s)`);
  console.log(`      Unchanged: ${comparisons.unchanged.length} file(s)`);
  console.log('');

  // Apply safe updates
  if (comparisons.safeToUpdate.length > 0) {
    console.log('   ✅ Applying safe updates...');
    for (const item of comparisons.safeToUpdate) {
      try {
        fs.copyFileSync(item.source, item.file);
        console.log(`      Updated: ${item.file}`);
        updateCount++;
      } catch (error) {
        console.error(`      ⚠️  Failed to update ${item.file}: ${error.message}`);
      }
    }
    console.log('');
  }

  // Copy new files
  if (comparisons.newFiles.length > 0) {
    console.log('   ➕ Adding new files...');
    for (const item of comparisons.newFiles) {
      try {
        // Ensure directory exists
        const dir = path.dirname(item.file);
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true });
        }
        fs.copyFileSync(item.source, item.file);
        console.log(`      Added: ${item.file}`);
        updateCount++;
      } catch (error) {
        console.error(`      ⚠️  Failed to add ${item.file}: ${error.message}`);
      }
    }
    console.log('');
  }

  // Save conflicts for manual review
  if (comparisons.conflicts.length > 0) {
    console.log('   ⚠️  Conflicts require manual review...');
    const conflictReport = generateConflictReport(comparisons.conflicts, templatePath);
    const conflictFile = path.join(UPGRADE_DIR, 'CONFLICTS.md');
    fs.writeFileSync(conflictFile, conflictReport, 'utf-8');
    console.log(`      Conflict report: ${conflictFile}`);
    console.log('');
  }

  console.log(`   Total files updated: ${updateCount}`);

  return updateCount;
}

/**
 * Generate conflict report
 */
function generateConflictReport(conflicts, templatePath) {
  let report = '# Template Upgrade Conflicts\n\n';
  report += 'The following files have conflicts that require manual review:\n\n';

  for (const conflict of conflicts) {
    report += `## ${conflict.file}\n\n`;
    report += `**Type**: ${conflict.type}\n`;
    report += `**Message**: ${conflict.message}\n\n`;
    report += '**Action Required**:\n';
    report += '1. Review changes in template version\n';
    report += `2. Template file location: ${path.join(templatePath, conflict.file)}\n`;
    report += '3. Manually merge changes if needed\n';
    report += '4. Test after merging\n\n';
    report += '---\n\n';
  }

  return report;
}

/**
 * Run migrations
 * Looks in template repo first (exact version match, then wildcard X.Y.x),
 * then falls back to project's scripts/migrations/ for custom migrations.
 */
async function runMigrations(fromVersion, toVersion, templatePath) {
  const migrationsRelDir = 'scripts/migrations';
  const [major, minor] = fromVersion.split('.');

  // Candidate filenames: exact match first, then wildcard (e.g. 1.8.x)
  const candidateNames = [
    `migrate-${fromVersion}-to-${toVersion}.js`,
    `migrate-${major}.${minor}.x-to-${toVersion}.js`
  ];

  // Search locations: template repo first, then project directory
  const searchDirs = [
    templatePath ? path.join(templatePath, migrationsRelDir) : null,
    migrationsRelDir
  ].filter(Boolean);

  let migrationFile = null;
  for (const filename of candidateNames) {
    for (const dir of searchDirs) {
      const candidate = path.join(dir, filename);
      if (fs.existsSync(candidate)) {
        migrationFile = candidate;
        break;
      }
    }
    if (migrationFile) break;
  }

  if (migrationFile) {
    console.log(`   Running migration: ${fromVersion} → ${toVersion}`);
    console.log(`   Script: ${migrationFile}`);
    try {
      require(path.resolve(migrationFile));
      console.log('   ✅ Migration complete');
    } catch (error) {
      console.error(`   ❌ Migration failed: ${error.message}`);
      throw error;
    }
  } else {
    console.log('   ℹ️  No migrations needed');
  }
}

/**
 * Update version file
 */
function updateVersion(fromVersion, toVersion) {
  const versionData = JSON.parse(fs.readFileSync(VERSION_FILE, 'utf-8'));

  versionData.previousVersion = fromVersion;
  versionData.version = toVersion;
  versionData.lastUpgrade = new Date().toISOString().split('T')[0];

  fs.writeFileSync(VERSION_FILE, JSON.stringify(versionData, null, 2), 'utf-8');

  console.log(`   Updated ${VERSION_FILE}`);
  console.log(`   Version: ${fromVersion} → ${toVersion}`);
}

/**
 * Display dry run results
 */
function displayDryRunResults(changes) {
  console.log('========================================');
  console.log('🔍 Dry Run Results');
  console.log('========================================');
  console.log('');
  console.log('The following changes would be applied:');
  console.log('');

  displayChangeSummary(changes);

  console.log('');
  console.log('No actual changes were made.');
  console.log('Run without --dry-run to apply these changes.');
  console.log('');
}

// Run main function
if (require.main === module) {
  main().catch(error => {
    console.error('');
    console.error('❌ Fatal error:', error.message);
    console.error(error.stack);
    console.error('');
    process.exit(1);
  });
}

module.exports = { main, getCurrentVersion, compareVersions, analyzeChanges };
