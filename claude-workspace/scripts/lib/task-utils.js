#!/usr/bin/env node

/**
 * Task Utilities Library
 *
 * Core utilities for multi-file task tracking system.
 * Handles frontmatter parsing, index generation, validation, and file operations.
 */

const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

// ==================== FRONTMATTER PARSING ====================

/**
 * Parse YAML frontmatter from markdown content
 * @param {string} content - Markdown content with frontmatter
 * @returns {{frontmatter: object, body: string}} Parsed frontmatter and body
 */
function parseFrontmatter(content) {
  // Normalize line endings to \n (handles Windows \r\n)
  const normalized = content.replace(/\r\n/g, '\n');
  const match = normalized.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) {
    throw new Error('Invalid frontmatter format. Expected:\n---\nkey: value\n---\nBody content');
  }

  const [, frontmatterYaml, body] = match;

  try {
    const frontmatter = yaml.parse(frontmatterYaml);
    return { frontmatter, body };
  } catch (error) {
    throw new Error(`Failed to parse YAML frontmatter: ${error.message}`);
  }
}

/**
 * Stringify frontmatter and body into markdown content
 * @param {object} frontmatter - Frontmatter object
 * @param {string} body - Body content
 * @returns {string} Markdown content with frontmatter
 */
function stringifyFrontmatter(frontmatter, body) {
  const frontmatterYaml = yaml.stringify(frontmatter);
  return `---\n${frontmatterYaml}---\n${body}`;
}

// ==================== INDEX GENERATION ====================

/**
 * Get all tasks from docs/tasks/ directory.
 * Each task is a subdirectory containing task.md (e.g., docs/tasks/TASK-001/task.md).
 * @param {string} tasksDir - Path to tasks directory (default: docs/tasks)
 * @returns {Array<object>} Array of task objects with frontmatter and filename
 */
function getAllTasks(tasksDir = 'docs/tasks') {
  if (!fs.existsSync(tasksDir)) {
    return [];
  }

  const entries = fs.readdirSync(tasksDir, { withFileTypes: true });
  const taskDirs = entries
    .filter(entry => entry.isDirectory())
    .map(entry => entry.name)
    .sort();

  const tasks = [];
  for (const dirName of taskDirs) {
    const taskFilePath = path.join(tasksDir, dirName, 'task.md');
    if (!fs.existsSync(taskFilePath)) continue;

    const content = fs.readFileSync(taskFilePath, 'utf-8');

    try {
      const { frontmatter } = parseFrontmatter(content);
      tasks.push({
        ...frontmatter,
        filename: `${dirName}/task.md`,
        filepath: taskFilePath
      });
    } catch (error) {
      console.warn(`Warning: Skipping invalid task file ${taskFilePath}: ${error.message}`);
    }
  }

  return tasks;
}

/**
 * Group tasks by a specific field
 * @param {Array<object>} tasks - Array of task objects
 * @param {string} field - Field name to group by (e.g., 'status', 'priority')
 * @returns {Record<string, Array<object>>} Tasks grouped by field value
 */
function groupBy(tasks, field) {
  return tasks.reduce((groups, task) => {
    const key = task[field] || 'Unknown';
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(task);
    return groups;
  }, {});
}

/**
 * Generate statistics from tasks
 * @param {Array<object>} tasks - Array of task objects
 * @returns {object} Statistics object
 */
function generateStatistics(tasks) {
  const byStatus = groupBy(tasks, 'status');
  const byPriority = groupBy(tasks, 'priority');
  const byAgent = groupBy(tasks.filter(t => t.assigned), 'assigned');

  return {
    total: tasks.length,
    byStatus,
    byPriority,
    byAgent
  };
}

/**
 * Regenerate the index file (docs/tasks/dashboard.md) from individual task files.
 * @param {string} tasksDir - Path to tasks directory (default: docs/tasks)
 * @param {string} indexPath - Path to index file (default: docs/tasks/dashboard.md)
 */
function regenerateIndexFile(tasksDir = 'docs/tasks', indexPath = 'docs/tasks/dashboard.md') {
  const allTasks = getAllTasks(tasksDir);

  const stats = generateStatistics(allTasks);

  // Separate by type
  const features = allTasks.filter(t => t.type !== 'bug');
  const bugs = allTasks.filter(t => t.type === 'bug');
  const activeTasks = features.filter(t => t.status !== 'DONE');
  const completedTasks = features.filter(t => t.status === 'DONE');
  const openBugs = bugs.filter(t => t.status !== 'DONE');

  const statusOrder = ['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'CLARIFICATION_NEEDED', 'IN_TESTING', 'DOCUMENTING', 'BLOCKED', 'DONE'];
  const priorityOrder = ['High', 'Medium', 'Low'];

  // Build markdown content
  let markdown = `# Task Tracking Dashboard

**Last Updated**: ${getCurrentTimestamp()} (auto-generated)

> **⚠️ Note**: This file is auto-generated. Do not edit manually.
> To update task status, use: \`/task-status TASK-ID STATUS\`
> To create new tasks, use: \`/task-create TASK-ID "Title" Priority Type\`

---

## Statistics

| Metric | Count |
|--------|-------|
| **Total Tasks** | ${stats.total} |
`;

  for (const status of statusOrder) {
    if (stats.byStatus[status]) {
      markdown += `| **${status}** | ${stats.byStatus[status].length} |\n`;
    }
  }

  markdown += `\n### By Priority\n\n`;
  for (const priority of priorityOrder) {
    if (stats.byPriority[priority]) {
      markdown += `- **${priority}**: ${stats.byPriority[priority].length} tasks\n`;
    }
  }

  markdown += `\n### By Agent\n\n`;
  const agents = Object.keys(stats.byAgent).sort();
  for (const agent of agents) {
    const agentTasks = stats.byAgent[agent];
    const taskIds = agentTasks.map(t => t.id).join(', ');
    markdown += `- **${agent}**: ${agentTasks.length} tasks (${taskIds})\n`;
  }

  markdown += `\n---\n\n## Active Tasks\n\n`;

  const activeByPriority = groupBy(activeTasks, 'priority');

  for (const priority of priorityOrder) {
    if (!activeByPriority[priority] || activeByPriority[priority].length === 0) continue;

    const icon = priority === 'High' ? '🔴' : priority === 'Medium' ? '🟡' : '🟢';
    markdown += `### ${icon} ${priority} Priority\n\n`;

    const byStatus = groupBy(activeByPriority[priority], 'status');

    for (const status of statusOrder) {
      if (!byStatus[status] || byStatus[status].length === 0) continue;

      markdown += `#### ${status}\n\n`;

      for (const task of byStatus[status]) {
        const workflowBadge = task.workflow === 'fast-track' ? ' ⚡' : '';
        markdown += `- **[${task.id}](tasks/${task.filename})** - ${task.title}${workflowBadge}\n`;
        markdown += `  - **Assigned**: ${task.assigned || 'Unassigned'}\n`;
        if (task.workflow === 'fast-track') markdown += `  - **Workflow**: ⚡ Fast-Track\n`;
        if (task.branch) markdown += `  - **Branch**: \`${task.branch}\`\n`;
        if (task.blocked_reason) markdown += `  - **⚠️ Blocked**: ${task.blocked_reason}\n`;
        markdown += `\n`;
      }
    }
  }

  // Completed Tasks
  if (completedTasks.length > 0) {
    markdown += `---\n\n## Completed Tasks\n\n`;

    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const recentlyCompleted = completedTasks.filter(t => {
      if (!t.updated) return false;
      return new Date(t.updated) >= sevenDaysAgo;
    });

    if (recentlyCompleted.length > 0) {
      markdown += `### Recently Completed (Last 7 Days)\n\n`;
      for (const task of recentlyCompleted) {
        markdown += `- **[${task.id}](tasks/${task.filename})** - ${task.title}\n`;
        markdown += `  - **Completed**: ${task.updated}\n`;
        markdown += `\n`;
      }
    } else {
      markdown += `### All Completed Tasks (${completedTasks.length})\n\n`;
      for (const task of completedTasks.slice(0, 10)) {
        markdown += `- **[${task.id}](tasks/${task.filename})** - ${task.title}\n`;
        markdown += `\n`;
      }
      if (completedTasks.length > 10) {
        markdown += `*... and ${completedTasks.length - 10} more completed tasks*\n`;
      }
    }
  }

  // Bug Tracking
  if (openBugs.length > 0) {
    markdown += `\n---\n\n## Bug Tracking\n\n`;
    markdown += `### Open Bugs (${openBugs.length})\n\n`;

    const bugsBySeverity = groupBy(openBugs, 'severity');
    const severityOrder = ['Critical', 'High', 'Medium', 'Low'];

    for (const severity of severityOrder) {
      if (!bugsBySeverity[severity] || bugsBySeverity[severity].length === 0) continue;
      markdown += `#### ${severity} Severity\n\n`;
      for (const bug of bugsBySeverity[severity]) {
        markdown += `- **[${bug.id}](tasks/${bug.filename})** - ${bug.title}\n`;
        markdown += `  - **Priority**: ${bug.priority || 'Not Set'} | **Assigned**: ${bug.assigned || 'Unassigned'}\n`;
        markdown += `\n`;
      }
    }

    if (bugsBySeverity.Unknown && bugsBySeverity.Unknown.length > 0) {
      for (const bug of bugsBySeverity.Unknown) {
        markdown += `- **[${bug.id}](tasks/${bug.filename})** - ${bug.title}\n`;
        markdown += `  - **Priority**: ${bug.priority || 'Not Set'} | **Assigned**: ${bug.assigned || 'Unassigned'}\n`;
        markdown += `\n`;
      }
    }
  }

  markdown += `\n---\n\n**💡 Tip**: Click on any task ID to view full details.\n`;

  // Write index file
  fs.writeFileSync(indexPath, markdown, 'utf-8');
  console.log(`✅ Index file regenerated: ${indexPath}`);
}

// ==================== VALIDATION ====================

/**
 * Validate task ID format
 * @param {string} taskId - Task ID to validate
 * @throws {Error} If task ID is invalid
 */
function validateTaskId(taskId) {
  const validPattern = /^(TASK|BUG|DEBT)-\d{3}$/;
  if (!validPattern.test(taskId)) {
    throw new Error(
      `Invalid task ID: ${taskId}\n` +
      `Expected format: TASK-XXX, BUG-XXX, or DEBT-XXX (e.g., TASK-001, BUG-042)`
    );
  }
}

/**
 * Validate status transition
 * @param {string} currentStatus - Current status
 * @param {string} newStatus - New status
 * @throws {Error} If transition is invalid
 */
function validateStatusTransition(currentStatus, newStatus) {
  const validTransitions = {
    'TODO': ['IN_PROGRESS', 'BLOCKED'],
    'IN_PROGRESS': ['IN_REVIEW', 'BLOCKED'],
    'IN_REVIEW': ['IN_TESTING', 'IN_PROGRESS', 'CLARIFICATION_NEEDED', 'DONE', 'BLOCKED'], // DONE for fast-track, CLARIFICATION_NEEDED for reviewer questions
    'CLARIFICATION_NEEDED': ['IN_REVIEW'], // After answering, return to review
    'IN_TESTING': ['DOCUMENTING', 'IN_PROGRESS', 'BLOCKED'],
    'DOCUMENTING': ['DONE', 'BLOCKED'],
    'BLOCKED': ['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'IN_TESTING', 'DOCUMENTING'],
    'DONE': [] // Can't transition from DONE
  };

  if (!validTransitions[currentStatus]) {
    throw new Error(`Unknown current status: ${currentStatus}`);
  }

  if (!validTransitions[currentStatus].includes(newStatus)) {
    throw new Error(
      `Invalid status transition: ${currentStatus} → ${newStatus}\n` +
      `Valid transitions from ${currentStatus}: ${validTransitions[currentStatus].join(', ')}`
    );
  }
}

/**
 * Get agent for a given status
 * @param {string} status - Task status
 * @returns {string} Agent name
 */
function getAgentForStatus(status) {
  const agentMap = {
    'TODO': 'Unassigned',
    'IN_PROGRESS': 'Code Implementation Agent',
    'IN_REVIEW': 'Code Review Agent',
    'CLARIFICATION_NEEDED': 'Code Implementation Agent', // Developer answers reviewer's questions
    'IN_TESTING': 'Test Agent',
    'DOCUMENTING': 'Documentation Agent',
    'DONE': 'None',
    'BLOCKED': null // Keep current assignment
  };

  return agentMap[status] || 'Unassigned';
}

// ==================== UTILITIES ====================

/**
 * Get current date in YYYY-MM-DD format
 * @returns {string} Current date
 */
function getCurrentDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Get current timestamp in YYYY-MM-DD HH:mm:ss format
 * @returns {string} Current timestamp
 */
function getCurrentTimestamp() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

/**
 * Add timestamp to task body for a specific phase
 * @param {string} body - Task body content
 * @param {string} status - New status
 * @returns {string} Updated body with timestamp
 */
function addTimestampToBody(body, status) {
  const timestamp = getCurrentTimestamp();
  const timestampLabels = {
    'IN_PROGRESS': 'Started',
    'IN_REVIEW': 'Review Started',
    'CLARIFICATION_NEEDED': 'Clarification Requested',
    'IN_TESTING': 'Testing Started',
    'DOCUMENTING': 'Documentation Started',
    'DONE': 'Completed'
  };

  const label = timestampLabels[status];
  if (!label) return body;

  // Find the Timestamps section
  const timestampsMatch = body.match(/(## Timestamps\n)([\s\S]*?)(\n## |$)/);
  if (timestampsMatch) {
    const [fullMatch, header, content, nextSection] = timestampsMatch;

    // Check if this timestamp already exists
    if (content.includes(`**${label}**:`)) {
      // Update existing timestamp
      const updatedContent = content.replace(
        new RegExp(`\\*\\*${label}\\*\\*:.*`),
        `**${label}**: ${timestamp}`
      );
      return body.replace(fullMatch, `${header}${updatedContent}${nextSection}`);
    } else {
      // Add new timestamp
      const updatedContent = `${content}- **${label}**: ${timestamp}\n`;
      return body.replace(fullMatch, `${header}${updatedContent}${nextSection}`);
    }
  }

  return body;
}

// ==================== EXPORTS ====================

module.exports = {
  // Frontmatter
  parseFrontmatter,
  stringifyFrontmatter,

  // Index generation
  getAllTasks,
  groupBy,
  generateStatistics,
  regenerateIndexFile,

  // Validation
  validateTaskId,
  validateStatusTransition,
  getAgentForStatus,

  // Utilities
  getCurrentDate,
  getCurrentTimestamp,
  addTimestampToBody
};
