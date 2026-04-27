#!/usr/bin/env node

/**
 * Publish Lesson Learned Skill
 *
 * Publishes technical lessons learned to VISSoft Confluence page 147621793
 * and creates local backup in docs/lessons-learned/
 *
 * Usage: node publish-lesson-learn.js [--interactive]
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Configuration
const CONFLUENCE_PAGE_ID = '147621793';
const LESSONS_DIR = 'docs/lessons-learned';
const LESSONS_INDEX = path.join(LESSONS_DIR, 'README.md');

// Confluence page structure
const CONFLUENCE_SPACE = 'TECH';
const CONFLUENCE_BASE_URL = 'https://vissoft.atlassian.net';

console.log('');
console.log('========================================');
console.log('📚 Publish Lesson Learned');
console.log('========================================');
console.log('');

// Ensure lessons directory exists
if (!fs.existsSync(LESSONS_DIR)) {
  console.log(`📁 Creating directory: ${LESSONS_DIR}`);
  fs.mkdirSync(LESSONS_DIR, { recursive: true });
}

// Get next lesson ID
function getNextLessonId() {
  const files = fs.readdirSync(LESSONS_DIR)
    .filter(f => f.match(/^LESSON-\d{3}\.md$/));

  if (files.length === 0) {
    return 'LESSON-001';
  }

  const numbers = files.map(f => {
    const match = f.match(/LESSON-(\d{3})/);
    return parseInt(match[1], 10);
  });

  const maxNumber = Math.max(...numbers);
  const nextNumber = String(maxNumber + 1).padStart(3, '0');
  return `LESSON-${nextNumber}`;
}

// Get current date
function getCurrentDate() {
  const now = new Date();
  return now.toISOString().split('T')[0]; // YYYY-MM-DD
}

// Get current timestamp
function getCurrentTimestamp() {
  const now = new Date();
  return now.toISOString().replace('T', ' ').split('.')[0]; // YYYY-MM-DD HH:mm:ss
}

// Prompt user for input
function prompt(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise(resolve => {
    rl.question(question, answer => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

// Prompt for multiline input
function promptMultiline(question) {
  console.log(question);
  console.log('(Enter your text, then press Ctrl+D on a new line when done)');
  console.log('---');

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  const lines = [];

  return new Promise(resolve => {
    rl.on('line', line => {
      lines.push(line);
    });

    rl.on('close', () => {
      resolve(lines.join('\n').trim());
    });
  });
}

// Convert markdown to Confluence storage format (XHTML)
function markdownToConfluence(markdown, lessonId) {
  // Simple markdown to Confluence XHTML converter
  // This is a basic implementation - can be enhanced with a proper markdown parser

  let html = markdown;

  // Headers
  html = html.replace(/^# (.+)$/gm, '<h2 id="' + lessonId.toLowerCase() + '">$1</h2>');
  html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Code blocks
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    const language = lang || 'text';
    return `<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">${language}</ac:parameter>
  <ac:plain-text-body><![CDATA[${code.trim()}]]></ac:plain-text-body>
</ac:structured-macro>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Unordered lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>\n$&</ul>\n');

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ol>\n$&</ol>\n');

  // Paragraphs (lines not already in tags)
  html = html.split('\n').map(line => {
    if (line.trim() === '') return '';
    if (line.match(/^<(h\d|ul|ol|li|ac:|code|strong|em)/)) return line;
    return `<p>${line}</p>`;
  }).join('\n');

  return html;
}

// Create local lesson learned file
function createLocalFile(lessonId, data) {
  const fileName = `${lessonId}.md`;
  const filePath = path.join(LESSONS_DIR, fileName);

  // Create frontmatter
  const frontmatter = `---
id: ${lessonId}
date: ${getCurrentDate()}
category: ${data.category}
severity: ${data.severity}
author: ${data.author || 'AI Agent'}
tags: [${data.tags || ''}]
confluence_page: ${CONFLUENCE_PAGE_ID}
---
`;

  // Create body
  const body = `# ${lessonId}: ${data.title}

## Problem

${data.problem}

## Root Cause

${data.rootCause}

## Solution

${data.solution}

${data.codeExample ? `\n**Configuration/Code:**\n\`\`\`${data.codeLanguage || 'text'}\n${data.codeExample}\n\`\`\`\n` : ''}

## Key Takeaways

${data.keyTakeaways}

## References

${data.references || '- None'}

---

**Published to Confluence**: ${getCurrentTimestamp()}
**Page**: [Lessons Learned](${CONFLUENCE_BASE_URL}/wiki/spaces/${CONFLUENCE_SPACE}/pages/${CONFLUENCE_PAGE_ID})
`;

  const content = frontmatter + '\n' + body;

  fs.writeFileSync(filePath, content, 'utf-8');
  console.log(`✅ Local file created: ${filePath}`);

  return content;
}

// Update lessons index
function updateLessonsIndex(lessonId, title, category, date) {
  if (!fs.existsSync(LESSONS_INDEX)) {
    // Create index if doesn't exist
    const indexContent = `# Lessons Learned Index

This directory contains technical lessons learned from difficult or special issues.

**Confluence Page**: [Lessons Learned - Technical Issues](${CONFLUENCE_BASE_URL}/wiki/spaces/${CONFLUENCE_SPACE}/pages/${CONFLUENCE_PAGE_ID})

## All Lessons

`;
    fs.writeFileSync(LESSONS_INDEX, indexContent, 'utf-8');
  }

  // Append new entry
  const entry = `- **[${lessonId}](${lessonId}.md)**: ${title} _(${category}, ${date})_\n`;
  fs.appendFileSync(LESSONS_INDEX, entry, 'utf-8');
  console.log(`✅ Index updated: ${LESSONS_INDEX}`);
}

// Generate Confluence content
function generateConfluenceContent(lessonId, data) {
  const markdown = `# ${lessonId}: ${data.title}

**Date:** ${getCurrentDate()} | **Category:** ${data.category} | **Severity:** ${data.severity}

## Problem

${data.problem}

## Root Cause

${data.rootCause}

## Solution

${data.solution}

${data.codeExample ? `\n\`\`\`${data.codeLanguage || 'text'}\n${data.codeExample}\n\`\`\`\n` : ''}

## Key Takeaways

${data.keyTakeaways}
`;

  return markdownToConfluence(markdown, lessonId);
}

// Prepare Confluence TOC entry
function generateTocEntry(lessonId, title) {
  return `<li><a href="#${lessonId.toLowerCase()}">${lessonId}: ${title}</a></li>`;
}

// Main execution
async function main() {
  console.log('This skill will guide you through creating a lesson learned entry.');
  console.log('');

  // Get lesson ID
  const lessonId = getNextLessonId();
  console.log(`📝 Creating lesson: ${lessonId}`);
  console.log('');

  // Gather information
  const title = await prompt('Issue title (brief): ');
  const category = await prompt('Category (Database/API/Performance/Security/Infrastructure/Integration/Frontend/Backend): ');
  const severity = await prompt('Severity (Low/Medium/High/Critical): ');
  const problem = await prompt('Problem description (one line): ');
  const rootCause = await prompt('Root cause (one line): ');
  const solution = await prompt('Solution (one line): ');

  console.log('');
  const hasCodeExample = await prompt('Include code example? (y/n): ');
  let codeExample = '';
  let codeLanguage = '';

  if (hasCodeExample.toLowerCase() === 'y') {
    codeLanguage = await prompt('Code language (java/javascript/python/sql/bash/etc): ');
    console.log('');
    console.log('Paste code example (Ctrl+D when done):');
    codeExample = await promptMultiline('');
  }

  console.log('');
  const keyTakeaways = await prompt('Key takeaways (comma-separated points): ');
  const references = await prompt('References (optional, comma-separated): ');
  const tags = await prompt('Tags (comma-separated, optional): ');

  const data = {
    title,
    category,
    severity,
    problem,
    rootCause,
    solution,
    codeExample,
    codeLanguage,
    keyTakeaways,
    references,
    tags,
    author: 'AI Agent'
  };

  console.log('');
  console.log('========================================');
  console.log('Processing...');
  console.log('========================================');
  console.log('');

  // Create local file
  const localContent = createLocalFile(lessonId, data);

  // Update index
  updateLessonsIndex(lessonId, title, category, getCurrentDate());

  // Generate Confluence content
  const confluenceContent = generateConfluenceContent(lessonId, data);
  const tocEntry = generateTocEntry(lessonId, title);

  // Save Confluence content for manual publish (MCP integration would go here)
  const tempFile = path.join(LESSONS_DIR, `${lessonId}-confluence.html`);
  const fullConfluenceContent = `<!-- Table of Contents Entry -->
${tocEntry}

<!-- Lesson Content (append to end of page) -->
${confluenceContent}
`;

  fs.writeFileSync(tempFile, fullConfluenceContent, 'utf-8');

  console.log('');
  console.log('========================================');
  console.log('✅ Lesson Learned Created!');
  console.log('========================================');
  console.log('');
  console.log(`📄 Local File: ${lessonId}.md`);
  console.log(`📄 Index Updated: README.md`);
  console.log(`📄 Confluence Content: ${lessonId}-confluence.html`);
  console.log('');
  console.log('Next Steps:');
  console.log('1. Review the local file for accuracy');
  console.log('2. Use Confluence MCP to publish (or manually copy content):');
  console.log('');
  console.log('   **Using MCP (Automated):**');
  console.log(`   mcp__atlassian__confluence_get_page(pageId: "${CONFLUENCE_PAGE_ID}")`);
  console.log('   - Add TOC entry from confluence.html file');
  console.log('   - Append lesson content to end of page');
  console.log(`   mcp__atlassian__confluence_update_page(...)`);
  console.log('');
  console.log('   **Manual (Fallback):**');
  console.log(`   - Open: ${CONFLUENCE_BASE_URL}/wiki/spaces/${CONFLUENCE_SPACE}/pages/${CONFLUENCE_PAGE_ID}`);
  console.log(`   - Copy content from: ${tempFile}`);
  console.log('   - Add TOC entry to Table of Contents section');
  console.log('   - Append lesson content to end of page');
  console.log('');
  console.log(`3. Commit changes: git add ${LESSONS_DIR} && git commit -m "docs: add ${lessonId}"`);
  console.log('');

  // Return data for potential MCP integration
  return {
    lessonId,
    localFile: path.join(LESSONS_DIR, `${lessonId}.md`),
    confluenceFile: tempFile,
    tocEntry,
    confluenceContent,
    pageId: CONFLUENCE_PAGE_ID
  };
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('');
    console.error('❌ Error:', error.message);
    console.error('');
    process.exit(1);
  });
}

module.exports = { main, generateConfluenceContent, generateTocEntry, markdownToConfluence };
