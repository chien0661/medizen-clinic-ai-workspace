#!/usr/bin/env node

/**
 * Task Status Update Script
 *
 * Updates task status in individual task files and regenerates the index.
 * Usage: node task-status.js TASK-ID STATUS [REASON]
 */

const fs = require('fs');
const path = require('path');
const {
  parseFrontmatter,
  stringifyFrontmatter,
  validateTaskId,
  validateStatusTransition,
  getAgentForStatus,
  getCurrentDate,
  getCurrentTimestamp,
  addTimestampToBody,
  regenerateIndexFile
} = require('../../scripts/lib/task-utils.js');

// Parse command-line arguments
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node task-status.js TASK-ID STATUS [REASON]');
  console.error('');
  console.error('Examples:');
  console.error('  node task-status.js TASK-001 IN_PROGRESS');
  console.error('  node task-status.js TASK-001 BLOCKED "Waiting for API approval"');
  console.error('  node task-status.js TASK-001,TASK-002,TASK-003 TODO');
  process.exit(1);
}

const taskIdsString = args[0];
const newStatus = args[1];
const reason = args.slice(2).join(' '); // Join remaining args as reason

// Split task IDs (supports bulk updates)
const taskIds = taskIdsString.split(',').map(id => id.trim());

// Process each task
for (const taskId of taskIds) {
  try {
    updateTaskStatus(taskId, newStatus, reason);
  } catch (error) {
    console.error(`❌ Error updating ${taskId}: ${error.message}`);
    process.exit(1);
  }
}

// Regenerate index after all updates
try {
  regenerateIndexFile();
  console.log('✅ Index file regenerated');
} catch (error) {
  console.error(`⚠️  Warning: Failed to regenerate index: ${error.message}`);
}

console.log(`\n✅ Successfully updated ${taskIds.length} task(s)`);

/**
 * Update task status for a single task
 * @param {string} taskId - Task ID (e.g., TASK-001)
 * @param {string} newStatus - New status
 * @param {string} reason - Optional reason (for BLOCKED status)
 */
function updateTaskStatus(taskId, newStatus, reason) {
  // Validate task ID format
  validateTaskId(taskId);

  // Construct task file path (new structure: docs/tasks/TASK-XXX/task.md)
  const taskFile = path.join('docs', 'tasks', taskId, 'task.md');

  // Check if task file exists
  if (!fs.existsSync(taskFile)) {
    throw new Error(
      `Task file not found: ${taskFile}\n` +
      `Did you mean to create a new task? Use: /task-create ${taskId} "Title" Priority Type`
    );
  }

  // Read task file
  const content = fs.readFileSync(taskFile, 'utf-8');

  // Parse frontmatter and body (with recovery guidance on failure)
  let frontmatter, body;
  try {
    ({ frontmatter, body } = parseFrontmatter(content));
  } catch (parseError) {
    throw new Error(
      `Failed to parse ${taskFile}: ${parseError.message}\n` +
      `The task file may have corrupted YAML frontmatter.\n` +
      `Fix: Open the file and ensure it starts with ---\\nkey: value\\n---`
    );
  }

  // Validate status transition
  const currentStatus = frontmatter.status;
  validateStatusTransition(currentStatus, newStatus);

  // Update frontmatter
  frontmatter.status = newStatus;
  frontmatter.updated = getCurrentDate();

  // Update assigned agent (unless BLOCKED, then keep current)
  const newAgent = getAgentForStatus(newStatus);
  if (newAgent !== null) {
    frontmatter.assigned = newAgent;
  }

  // Handle BLOCKED status
  if (newStatus === 'BLOCKED') {
    if (!reason) {
      throw new Error(
        'BLOCKED status requires a reason.\n' +
        `Usage: /task-status ${taskId} BLOCKED "Reason for blocking"`
      );
    }
    frontmatter.blocked_reason = reason;
  } else {
    // Remove blocked_reason if no longer blocked
    delete frontmatter.blocked_reason;
  }

  // Add timestamp to body
  const updatedBody = addTimestampToBody(body, newStatus);

  // Write updated task file (atomic: write to temp, then rename)
  const updatedContent = stringifyFrontmatter(frontmatter, updatedBody);
  const tempFile = taskFile + '.tmp';
  try {
    fs.writeFileSync(tempFile, updatedContent, 'utf-8');
    fs.renameSync(tempFile, taskFile);
  } catch (writeError) {
    // Clean up temp file on failure
    try { fs.unlinkSync(tempFile); } catch {}
    throw new Error(`Failed to write ${taskFile}: ${writeError.message}`);
  }

  console.log(`✅ ${taskId}: ${currentStatus} → ${newStatus}`);
  if (newAgent !== null) {
    console.log(`   Assigned to: ${newAgent}`);
  }
  if (reason) {
    console.log(`   Reason: ${reason}`);
  }
}
