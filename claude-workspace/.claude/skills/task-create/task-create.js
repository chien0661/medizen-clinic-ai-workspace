#!/usr/bin/env node

/**
 * Task Create Script
 *
 * Creates a new task file from template and regenerates the index.
 * Usage: node task-create.js TASK-ID "Title" PRIORITY TYPE
 */

const fs = require('fs');
const path = require('path');
const {
  validateTaskId,
  getCurrentDate,
  regenerateIndexFile
} = require('../../../scripts/lib/task-utils.js');

// Parse command-line arguments
const args = process.argv.slice(2);
if (args.length < 4) {
  console.error('Usage: node task-create.js TASK-ID "Title" PRIORITY TYPE');
  console.error('');
  console.error('PRIORITY: High, Medium, or Low');
  console.error('TYPE: feature, bug, or debt');
  console.error('');
  console.error('Examples:');
  console.error('  node task-create.js TASK-001 "Implement User Profile API" High feature');
  console.error('  node task-create.js BUG-042 "Fix login timeout issue" High bug');
  console.error('  node task-create.js DEBT-001 "Refactor authentication logic" Medium debt');
  process.exit(1);
}

const taskId = args[0];
const title = args[1];
const priority = args[2];
const type = args[3];

try {
  createTask(taskId, title, priority, type);
} catch (error) {
  console.error(`❌ Error creating task: ${error.message}`);
  process.exit(1);
}

/**
 * Create a new task from template
 * @param {string} taskId - Task ID (e.g., TASK-001)
 * @param {string} title - Task title
 * @param {string} priority - Priority (High, Medium, Low)
 * @param {string} type - Type (feature, bug, debt)
 */
function createTask(taskId, title, priority, type) {
  // Validate task ID format
  validateTaskId(taskId);

  // Validate priority
  const validPriorities = ['High', 'Medium', 'Low'];
  if (!validPriorities.includes(priority)) {
    throw new Error(
      `Invalid priority: ${priority}\n` +
      `Valid values: ${validPriorities.join(', ')}`
    );
  }

  // Validate type
  const validTypes = ['feature', 'bug', 'debt'];
  if (!validTypes.includes(type)) {
    throw new Error(
      `Invalid type: ${type}\n` +
      `Valid values: ${validTypes.join(', ')}`
    );
  }

  // Ensure docs/tasks/ directory exists
  const tasksDir = path.join('docs', 'tasks');
  if (!fs.existsSync(tasksDir)) {
    fs.mkdirSync(tasksDir, { recursive: true });
    console.log(`✅ Created directory: ${tasksDir}`);
  }

  // Task folder and file path
  const taskDir = path.join(tasksDir, taskId);
  const taskFile = path.join(taskDir, 'task.md');

  // Check if task already exists
  if (fs.existsSync(taskDir)) {
    throw new Error(
      `Task folder already exists: ${taskDir}\n` +
      `Use /task-status to update existing tasks, or choose a different task ID`
    );
  }

  // Create task folder structure
  const subdirs = [
    'refs',
    'handoff',
    'bugs',
    path.join('deliveries', 'test-cases'),
    path.join('deliveries', 'test-reports'),
    path.join('deliveries', 'api-specs'),
    path.join('deliveries', 'sql-scripts'),
    path.join('deliveries', 'final-specs'),
  ];
  fs.mkdirSync(taskDir, { recursive: true });
  for (const subdir of subdirs) {
    fs.mkdirSync(path.join(taskDir, subdir), { recursive: true });
  }
  console.log(`✅ Created task folder: ${taskDir}`);

  // Read template
  const templatePath = path.join('docs', 'templates', 'task-template.md');
  if (!fs.existsSync(templatePath)) {
    throw new Error(
      `Template not found: ${templatePath}\n` +
      `Please ensure docs/templates/task-template.md exists`
    );
  }

  let template = fs.readFileSync(templatePath, 'utf-8');

  // Replace placeholders
  const currentDate = getCurrentDate();
  template = template
    .replace(/{{ID}}/g, taskId)
    .replace(/{{TITLE}}/g, title)
    .replace(/{{PRIORITY}}/g, priority)
    .replace(/{{TYPE}}/g, type)
    .replace(/{{CREATED}}/g, currentDate)
    .replace(/{{UPDATED}}/g, currentDate);

  // Write task file
  fs.writeFileSync(taskFile, template, 'utf-8');
  console.log(`✅ Created task file: ${taskFile}`);

  // Regenerate index
  try {
    regenerateIndexFile();
    console.log('✅ Index file regenerated');
  } catch (error) {
    console.error(`⚠️  Warning: Failed to regenerate index: ${error.message}`);
  }

  console.log('');
  console.log(`✅ Task ${taskId} created successfully!`);
  console.log('');
  console.log('Next steps:');
  console.log(`  1. Edit task file: ${taskFile}`);
  console.log(`  2. Fill in Description, Requirements, and Acceptance Criteria`);
  console.log(`  3. Start work: /task-status ${taskId} IN_PROGRESS`);
}
