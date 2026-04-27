#!/usr/bin/env node

/**
 * Migration Script: Single-File to Multi-File Task Tracking
 *
 * This script migrates from the old single-file task tracking system (docs/tasks/dashboard.md)
 * to the new multi-file system (docs/tasks/*.md with YAML frontmatter).
 *
 * Usage: node scripts/migrate-tasks-to-multifile.js
 */

const fs = require('fs');
const path = require('path');
const {
  getCurrentDate,
  regenerateIndexFile
} = require('./lib/task-utils.js');

const TASKS_FILE = 'docs/tasks/dashboard.md';
const TASKS_DIR = 'docs/tasks';
const BACKUP_FILE = 'docs/tasks/dashboard.md.backup';
const TEMPLATE_FILE = 'docs/templates/task-template.md';

console.log('');
console.log('========================================');
console.log('Task Tracking System Migration');
console.log('Single-File → Multi-File');
console.log('========================================');
console.log('');

// Step 1: Check if tasks.md exists
if (!fs.existsSync(TASKS_FILE)) {
  console.error('❌ Error: docs/tasks/dashboard.md not found');
  console.error('   This script requires an existing tasks.md file to migrate.');
  process.exit(1);
}

// Step 2: Create backup
console.log(`📦 Creating backup: ${BACKUP_FILE}`);
fs.copyFileSync(TASKS_FILE, BACKUP_FILE);
console.log('✅ Backup created');
console.log('');

// Step 3: Read and parse tasks.md
console.log('📖 Reading tasks from docs/tasks/dashboard.md...');
const tasksContent = fs.readFileSync(TASKS_FILE, 'utf-8');

// Parse tasks from the old format
const tasks = parseOldTasksFile(tasksContent);
console.log(`✅ Found ${tasks.length} task(s) to migrate`);
console.log('');

if (tasks.length === 0) {
  console.log('⚠️  No tasks found in docs/tasks/dashboard.md');
  console.log('   The file exists but contains no tasks to migrate.');
  console.log('   Migration aborted.');
  process.exit(0);
}

// Step 4: Create tasks directory
if (!fs.existsSync(TASKS_DIR)) {
  console.log(`📁 Creating directory: ${TASKS_DIR}`);
  fs.mkdirSync(TASKS_DIR, { recursive: true });
  console.log('✅ Directory created');
} else {
  console.log(`✅ Directory already exists: ${TASKS_DIR}`);
}
console.log('');

// Step 5: Check if template exists
if (!fs.existsSync(TEMPLATE_FILE)) {
  console.error(`❌ Error: Template not found: ${TEMPLATE_FILE}`);
  console.error('   Please ensure docs/templates/task-template.md exists.');
  process.exit(1);
}

// Step 6: Create individual task files
console.log('📝 Creating individual task files...');
let successCount = 0;
let errorCount = 0;

for (const task of tasks) {
  try {
    createTaskFile(task);
    console.log(`  ✅ ${task.id}.md`);
    successCount++;
  } catch (error) {
    console.error(`  ❌ ${task.id}.md: ${error.message}`);
    errorCount++;
  }
}

console.log('');
console.log(`✅ Successfully created ${successCount} task file(s)`);
if (errorCount > 0) {
  console.log(`⚠️  Failed to create ${errorCount} task file(s)`);
}
console.log('');

// Step 7: Generate new index
console.log('📊 Generating new index file...');
try {
  regenerateIndexFile();
  console.log('✅ Index file generated: docs/tasks/dashboard.md');
} catch (error) {
  console.error(`❌ Error generating index: ${error.message}`);
  console.error('   You may need to run this manually later.');
}

console.log('');
console.log('========================================');
console.log('Migration Complete!');
console.log('========================================');
console.log('');
console.log('✅ Tasks migrated:', successCount);
console.log('📁 Task files location: docs/tasks/');
console.log('📊 Dashboard location: docs/tasks/dashboard.md');
console.log('💾 Backup location:', BACKUP_FILE);
console.log('');
console.log('Next steps:');
console.log('1. Review the new task files in docs/tasks/');
console.log('2. Check the generated dashboard: docs/tasks/dashboard.md');
console.log('3. Test task operations:');
console.log('   - /task-status TASK-001 IN_PROGRESS');
console.log('   - /task-create TASK-999 "Test Task" High feature');
console.log('4. If everything works, you can delete the backup:');
console.log(`   rm ${BACKUP_FILE}`);
console.log('');

/**
 * Parse old tasks.md format to extract tasks
 * @param {string} content - Content of tasks.md
 * @returns {Array<object>} Array of task objects
 */
function parseOldTasksFile(content) {
  const tasks = [];

  // Split content by task headers (## TASK-XXX or ## BUG-XXX)
  const taskPattern = /^## (TASK|BUG|DEBT)-(\d{3}): (.+?)$/gm;
  const matches = [...content.matchAll(taskPattern)];

  for (let i = 0; i < matches.length; i++) {
    const match = matches[i];
    const nextMatch = matches[i + 1];

    // Extract task section
    const startIndex = match.index;
    const endIndex = nextMatch ? nextMatch.index : content.length;
    const taskSection = content.substring(startIndex, endIndex);

    const prefix = match[1]; // TASK, BUG, or DEBT
    const number = match[2]; // 001, 002, etc.
    const title = match[3].trim();
    const id = `${prefix}-${number}`;

    // Parse fields from task section
    const task = {
      id,
      type: prefix === 'BUG' ? 'bug' : prefix === 'DEBT' ? 'debt' : 'feature',
      title,
      status: extractField(taskSection, 'Status') || 'TODO',
      priority: extractField(taskSection, 'Priority') || 'Medium',
      assigned: extractField(taskSection, 'Assigned') || 'Unassigned',
      branch: extractField(taskSection, 'Branch') || '',
      created: extractField(taskSection, 'Created') || getCurrentDate(),
      body: taskSection
    };

    tasks.push(task);
  }

  return tasks;
}

/**
 * Extract field value from task section
 * @param {string} section - Task section content
 * @param {string} fieldName - Field name (e.g., "Status", "Priority")
 * @returns {string|null} Field value or null
 */
function extractField(section, fieldName) {
  const regex = new RegExp(`\\*\\*${fieldName}:\\*\\*\\s*(.+?)(?:\\n|$)`, 'i');
  const match = section.match(regex);
  return match ? match[1].trim() : null;
}

/**
 * Create individual task file from old format
 * @param {object} task - Task object
 */
function createTaskFile(task) {
  const taskFile = path.join(TASKS_DIR, `${task.id}.md`);

  // Check if file already exists
  if (fs.existsSync(taskFile)) {
    throw new Error('File already exists');
  }

  // Read template
  const template = fs.readFileSync(TEMPLATE_FILE, 'utf-8');

  // Replace placeholders
  const content = template
    .replace(/{{ID}}/g, task.id)
    .replace(/{{TITLE}}/g, task.title)
    .replace(/{{PRIORITY}}/g, task.priority)
    .replace(/{{TYPE}}/g, task.type)
    .replace(/{{CREATED}}/g, task.created)
    .replace(/{{UPDATED}}/g, getCurrentDate());

  // Parse frontmatter and body from template
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!frontmatterMatch) {
    throw new Error('Invalid template format');
  }

  let [, frontmatterContent, bodyContent] = frontmatterMatch;

  // Update frontmatter with actual values
  frontmatterContent = frontmatterContent
    .replace(/status: TODO/, `status: ${task.status}`)
    .replace(/assigned: Unassigned/, `assigned: ${task.assigned}`)
    .replace(/branch: ""/, task.branch ? `branch: "${task.branch}"` : 'branch: ""');

  // Try to extract description from old format
  const descriptionMatch = task.body.match(/\*\*Description:\*\*\s*(.+?)(?:\n\*\*|$)/s);
  if (descriptionMatch) {
    bodyContent = bodyContent.replace(
      /\[Provide a clear description of what needs to be done\]/,
      descriptionMatch[1].trim()
    );
  }

  // Reconstruct file content
  const finalContent = `---\n${frontmatterContent}\n---\n${bodyContent}`;

  // Write file
  fs.writeFileSync(taskFile, finalContent, 'utf-8');
}
