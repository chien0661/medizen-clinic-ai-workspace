#!/usr/bin/env node

/**
 * Release Skill Handler
 *
 * Automates the complete release process for AI Team Template repository
 *
 * Usage: /release VERSION TYPE
 * Example: /release 1.4.0 MINOR
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '../../..');

/**
 * Execute shell command and return output
 */
function exec(command, options = {}) {
  try {
    return execSync(command, {
      cwd: ROOT_DIR,
      encoding: 'utf-8',
      ...options
    }).trim();
  } catch (error) {
    throw new Error(`Command failed: ${command}\n${error.message}`);
  }
}

/**
 * Validate version format (X.X.X)
 */
function validateVersion(version) {
  const regex = /^\d+\.\d+\.\d+$/;
  if (!regex.test(version)) {
    throw new Error(`Invalid version format: ${version}. Expected: X.X.X (e.g., 1.4.0)`);
  }
  return true;
}

/**
 * Validate release type
 */
function validateType(type) {
  const validTypes = ['PATCH', 'MINOR', 'MAJOR'];
  if (!validTypes.includes(type.toUpperCase())) {
    throw new Error(`Invalid release type: ${type}. Expected: PATCH, MINOR, or MAJOR`);
  }
  return type.toUpperCase();
}

/**
 * Get current date in YYYY-MM-DD format
 */
function getToday() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Step 1: Validate Prerequisites
 */
function validatePrerequisites(version) {
  console.log('\n📋 Step 1: Validating prerequisites...\n');

  // Check git status
  const status = exec('git status --porcelain');
  if (status) {
    throw new Error('❌ Uncommitted changes detected. Please commit or stash changes first.');
  }
  console.log('   ✅ Git status clean');

  // Check branch
  const branch = exec('git branch --show-current');
  if (branch !== 'master') {
    throw new Error(`❌ Not on master branch (current: ${branch}). Switch to master first.`);
  }
  console.log('   ✅ On master branch');

  // Check [Unreleased] section in CHANGELOG
  const changelogPath = path.join(ROOT_DIR, 'CHANGELOG.md');
  const changelog = fs.readFileSync(changelogPath, 'utf-8');
  if (!changelog.includes('[Unreleased]')) {
    throw new Error('❌ No [Unreleased] section in CHANGELOG.md. Add changes first.');
  }
  console.log('   ✅ [Unreleased] section found in CHANGELOG.md');

  // Check if version already exists
  const tags = exec('git tag -l');
  if (tags.includes(`${version}-RELEASE`)) {
    throw new Error(`❌ Version ${version}-RELEASE already exists. Use a different version.`);
  }
  console.log(`   ✅ Version ${version} is available`);

  console.log('\n✅ All prerequisites validated\n');
}

/**
 * Step 2: Update CHANGELOG.md
 */
function updateChangelog(version) {
  console.log('\n📝 Step 2: Updating CHANGELOG.md...\n');

  const changelogPath = path.join(ROOT_DIR, 'CHANGELOG.md');
  let changelog = fs.readFileSync(changelogPath, 'utf-8');
  const today = getToday();

  // Replace [Unreleased] with version and date
  const unreleasedSection = `## [Unreleased]`;
  const versionSection = `## [Unreleased]\n\n---\n\n## [${version}] - ${today}`;

  if (!changelog.includes(unreleasedSection)) {
    throw new Error('❌ [Unreleased] section not found in CHANGELOG.md');
  }

  changelog = changelog.replace(unreleasedSection, versionSection);

  fs.writeFileSync(changelogPath, changelog, 'utf-8');
  console.log(`   ✅ Updated CHANGELOG.md: [${version}] - ${today}`);
  console.log('\n✅ CHANGELOG.md updated\n');
}

/**
 * Step 3: Update README.md
 */
function updateReadme(version) {
  console.log('\n📝 Step 3: Updating README.md...\n');

  const readmePath = path.join(ROOT_DIR, 'README.md');
  let readme = fs.readFileSync(readmePath, 'utf-8');
  const today = getToday();

  // Update version line (e.g., **Version**: 1.4.0 (2026-01-28))
  const versionRegex = /\*\*Version\*\*: \d+\.\d+\.\d+ \(\d{4}-\d{2}-\d{2}\)/;
  if (!versionRegex.test(readme)) {
    throw new Error('❌ Version line not found in README.md');
  }
  readme = readme.replace(versionRegex, `**Version**: ${version} (${today})`);
  console.log(`   ✅ Updated version: ${version} (${today})`);

  // Update "What's New" section (e.g., ## 🎯 What's New in 1.4.0-RELEASE (2026-01-28))
  const whatsNewRegex = /## 🎯 What's New in \d+\.\d+\.\d+-RELEASE \(\d{4}-\d{2}-\d{2}\)/;
  if (!whatsNewRegex.test(readme)) {
    throw new Error('❌ "What\'s New" section not found in README.md');
  }
  readme = readme.replace(whatsNewRegex, `## 🎯 What's New in ${version}-RELEASE (${today})`);
  console.log(`   ✅ Updated "What's New" section: ${version}-RELEASE`);

  fs.writeFileSync(readmePath, readme, 'utf-8');
  console.log('\n✅ README.md updated\n');
}

/**
 * Step 4: Get commit summary from CHANGELOG
 */
function getCommitSummary(version) {
  const changelogPath = path.join(ROOT_DIR, 'CHANGELOG.md');
  const changelog = fs.readFileSync(changelogPath, 'utf-8');

  // Extract section between [version] and next [version]
  const versionRegex = new RegExp(`## \\[${version}\\][\\s\\S]*?(?=## \\[|$)`);
  const match = changelog.match(versionRegex);

  if (!match) {
    throw new Error(`❌ Version [${version}] not found in CHANGELOG.md`);
  }

  const section = match[0];

  // Extract first line after version (usually a brief description)
  const lines = section.split('\n').filter(line => line.trim());

  // Try to find a title or use first meaningful content
  let summary = 'Release updates';
  for (const line of lines) {
    if (line.startsWith('###') || line.startsWith('-')) {
      summary = line.replace(/^###\s*/, '').replace(/^-\s*/, '').trim();
      if (summary.length > 60) {
        summary = summary.substring(0, 60) + '...';
      }
      break;
    }
  }

  return summary;
}

/**
 * Step 5: Stage changes
 */
function stageChanges() {
  console.log('\n📦 Step 4: Staging changes...\n');

  exec('git add CHANGELOG.md README.md');
  console.log('   ✅ Staged CHANGELOG.md and README.md');

  // Check if there are other modified files that should be included
  const status = exec('git status --porcelain');
  if (status) {
    console.log('\n   ℹ️  Other modified files detected:');
    status.split('\n').forEach(line => {
      if (!line.includes('CHANGELOG.md') && !line.includes('README.md')) {
        console.log(`      ${line}`);
      }
    });
    console.log('\n   ⚠️  Only CHANGELOG.md and README.md will be committed.');
    console.log('      If other files should be included, stage them manually after this script fails.\n');
  }

  console.log('\n✅ Changes staged\n');
}

/**
 * Step 6: Create release commit
 */
function createCommit(version) {
  console.log('\n💾 Step 5: Creating release commit...\n');

  const summary = getCommitSummary(version);
  const commitMessage = `release: version ${version} - ${summary}

Changes documented in CHANGELOG.md [${version}] section.`;

  // Create commit
  exec(`git commit -m "${commitMessage.replace(/"/g, '\\"')}"`);

  const commitHash = exec('git log -1 --format=%h');
  console.log(`   ✅ Commit created: ${commitHash}`);
  console.log(`   ✅ Message: release: version ${version} - ${summary}`);
  console.log('\n✅ Release commit created\n');
}

/**
 * Step 7: Create annotated tag
 */
function createTag(version) {
  console.log('\n🏷️  Step 6: Creating annotated tag...\n');

  const summary = getCommitSummary(version);
  const tagName = `${version}-RELEASE`;
  const tagMessage = `Version ${version} - ${summary}`;

  exec(`git tag -a ${tagName} -m "${tagMessage}"`);

  console.log(`   ✅ Tag created: ${tagName}`);
  console.log(`   ✅ Message: ${tagMessage}`);
  console.log('\n✅ Annotated tag created\n');

  return tagName;
}

/**
 * Step 8: Push to remote
 */
function pushToRemote(tagName) {
  console.log('\n🚀 Step 7: Pushing to remote...\n');

  // Push commit
  console.log('   📤 Pushing commit to master...');
  exec('git push origin master');
  console.log('   ✅ Commit pushed');

  // Push tag
  console.log(`   📤 Pushing tag ${tagName}...`);
  exec(`git push origin ${tagName}`);
  console.log('   ✅ Tag pushed');

  console.log('\n✅ Pushed to remote\n');
}

/**
 * Step 9: Send Telegram notification
 */
function sendTelegramNotification() {
  console.log('\n📢 Step 8: Sending Telegram notification...\n');

  const scriptPath = path.join(ROOT_DIR, 'scripts', 'send-release-notification.js');

  if (!fs.existsSync(scriptPath)) {
    throw new Error(`❌ Telegram notification script not found: ${scriptPath}`);
  }

  exec(`node "${scriptPath}"`);

  console.log('\n✅ Telegram notification sent\n');
}

/**
 * Step 10: Final verification
 */
function finalVerification(version, tagName) {
  console.log('\n✔️  Step 9: Final verification...\n');

  // Verify tag on remote
  const remoteTags = exec('git ls-remote --tags origin');
  if (!remoteTags.includes(tagName)) {
    throw new Error(`❌ Tag ${tagName} not found on remote`);
  }
  console.log(`   ✅ Tag ${tagName} verified on remote`);

  // Verify commit on remote
  const localCommit = exec('git log -1 --format=%H');
  const remoteCommit = exec('git log origin/master -1 --format=%H');
  if (localCommit !== remoteCommit) {
    throw new Error('❌ Local and remote commits do not match');
  }
  console.log('   ✅ Commit verified on remote');

  console.log('\n✅ All verifications passed\n');
}

/**
 * Main release process
 */
async function release(version, type) {
  console.log('\n' + '='.repeat(60));
  console.log('🚀 AI Team Template Release Automation');
  console.log('='.repeat(60));
  console.log(`\n   Version: ${version}`);
  console.log(`   Type: ${type}`);
  console.log(`   Date: ${getToday()}`);
  console.log('\n' + '='.repeat(60) + '\n');

  try {
    // Validate inputs
    validateVersion(version);
    validateType(type);

    // Execute release steps
    validatePrerequisites(version);
    updateChangelog(version);
    updateReadme(version);
    stageChanges();
    createCommit(version);
    const tagName = createTag(version);
    pushToRemote(tagName);
    sendTelegramNotification();
    finalVerification(version, tagName);

    // Success message
    console.log('\n' + '='.repeat(60));
    console.log('✨ RELEASE SUCCESSFUL ✨');
    console.log('='.repeat(60));
    console.log(`\n   Version: ${version}-RELEASE`);
    console.log(`   Tag: ${tagName}`);
    console.log(`   Commit: ${exec('git log -1 --format=%h')}`);
    console.log(`   Date: ${getToday()}`);
    console.log('\n   ✅ Commit pushed to master');
    console.log('   ✅ Tag pushed to remote');
    console.log('   ✅ Telegram notification sent');
    console.log('\n' + '='.repeat(60) + '\n');

    process.exit(0);

  } catch (error) {
    console.error('\n' + '='.repeat(60));
    console.error('❌ RELEASE FAILED');
    console.error('='.repeat(60));
    console.error(`\n${error.message}\n`);
    console.error('='.repeat(60) + '\n');
    process.exit(1);
  }
}

// Parse command line arguments
const args = process.argv.slice(2);

if (args.length !== 2) {
  console.error('\n❌ Invalid usage\n');
  console.error('Usage: /release VERSION TYPE');
  console.error('Example: /release 1.4.0 MINOR\n');
  console.error('Parameters:');
  console.error('  VERSION - Version number (e.g., 1.4.0)');
  console.error('  TYPE    - Release type: PATCH, MINOR, or MAJOR\n');
  process.exit(1);
}

const [version, type] = args;

// Run release
release(version, type);
