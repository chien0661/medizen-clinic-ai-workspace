#!/usr/bin/env node

/**
 * Publish Lesson Learned to Confluence via MCP
 *
 * This script uses Confluence MCP tools to automatically update page 147621793
 * with new lesson learned content.
 *
 * Usage: node publish-to-confluence.js <lesson-id>
 * Example: node publish-to-confluence.js LESSON-001
 */

const fs = require('fs');
const path = require('path');

const CONFLUENCE_PAGE_ID = '147621793';
const LESSONS_DIR = 'docs/lessons-learned';

// Parse command line arguments
const args = process.argv.slice(2);
const lessonId = args[0];

if (!lessonId) {
  console.error('❌ Error: Lesson ID required');
  console.error('Usage: node publish-to-confluence.js <lesson-id>');
  console.error('Example: node publish-to-confluence.js LESSON-001');
  process.exit(1);
}

const lessonFile = path.join(LESSONS_DIR, `${lessonId}.md`);
const confluenceFile = path.join(LESSONS_DIR, `${lessonId}-confluence.html`);

if (!fs.existsSync(lessonFile)) {
  console.error(`❌ Error: Lesson file not found: ${lessonFile}`);
  console.error('Run /publish-lesson-learn first to create the lesson.');
  process.exit(1);
}

if (!fs.existsSync(confluenceFile)) {
  console.error(`❌ Error: Confluence content file not found: ${confluenceFile}`);
  console.error('Run /publish-lesson-learn first to generate Confluence content.');
  process.exit(1);
}

console.log('');
console.log('========================================');
console.log('📤 Publishing to Confluence via MCP');
console.log('========================================');
console.log('');

console.log(`📄 Lesson: ${lessonId}`);
console.log(`📄 Local file: ${lessonFile}`);
console.log(`🌐 Target page: ${CONFLUENCE_PAGE_ID}`);
console.log('');

// Read Confluence content
const confluenceContent = fs.readFileSync(confluenceFile, 'utf-8');

// Extract TOC entry and lesson content
const tocMatch = confluenceContent.match(/<!-- Table of Contents Entry -->\s*([\s\S]*?)\s*<!-- Lesson Content/);
const contentMatch = confluenceContent.match(/<!-- Lesson Content.*?-->\s*([\s\S]*)/);

if (!tocMatch || !contentMatch) {
  console.error('❌ Error: Invalid Confluence content format');
  process.exit(1);
}

const tocEntry = tocMatch[1].trim();
const lessonContent = contentMatch[1].trim();

console.log('📋 Instructions for Claude Code:');
console.log('');
console.log('Use the following MCP tools to update Confluence:');
console.log('');
console.log('**Step 1: Read existing page**');
console.log('```');
console.log('mcp__atlassian__confluence_get_page');
console.log('Parameters:');
console.log(`  pageId: "${CONFLUENCE_PAGE_ID}"`);
console.log('  expand: ["body.storage", "version"]');
console.log('```');
console.log('');
console.log('**Step 2: Parse existing content**');
console.log('- Extract current page body');
console.log('- Find "Table of Contents" section (look for <h2>Table of Contents</h2>)');
console.log('- Find the closing </ul> tag of the TOC');
console.log('- Note the current version number');
console.log('');
console.log('**Step 3: Update content**');
console.log('');
console.log('**Add this TOC entry** (before closing </ul> of Table of Contents):');
console.log('```html');
console.log(tocEntry);
console.log('```');
console.log('');
console.log('**Append this content** (at end of page body, after all existing lessons):');
console.log('```html');
console.log(lessonContent);
console.log('```');
console.log('');
console.log('**Step 4: Update page via MCP**');
console.log('```');
console.log('mcp__atlassian__confluence_update_page');
console.log('Parameters:');
console.log(`  pageId: "${CONFLUENCE_PAGE_ID}"`);
console.log('  title: "Lessons Learned - Technical Issues" (keep same)');
console.log('  body: [updated body with TOC entry and new lesson]');
console.log('  version: [current version + 1]');
console.log('```');
console.log('');
console.log('========================================');
console.log('📝 Content Preview');
console.log('========================================');
console.log('');
console.log('**TOC Entry:**');
console.log(tocEntry);
console.log('');
console.log('**Lesson Content (first 500 chars):**');
console.log(lessonContent.substring(0, 500) + '...');
console.log('');

// Output structured data for Claude to use
const publishData = {
  pageId: CONFLUENCE_PAGE_ID,
  lessonId: lessonId,
  tocEntry: tocEntry,
  lessonContent: lessonContent,
  localFile: lessonFile,
  instructions: {
    step1: {
      tool: 'mcp__atlassian__confluence_get_page',
      params: {
        pageId: CONFLUENCE_PAGE_ID,
        expand: ['body.storage', 'version']
      }
    },
    step2: 'Parse existing body, find TOC section, note version',
    step3: {
      tocInsert: 'Insert tocEntry before closing </ul> of Table of Contents',
      contentAppend: 'Append lessonContent at end of body'
    },
    step4: {
      tool: 'mcp__atlassian__confluence_update_page',
      params: {
        pageId: CONFLUENCE_PAGE_ID,
        title: 'Lessons Learned - Technical Issues',
        body: '[updated body]',
        version: '[current version + 1]'
      }
    }
  }
};

// Save publish data for reference
const publishDataFile = path.join(LESSONS_DIR, `${lessonId}-publish-data.json`);
fs.writeFileSync(publishDataFile, JSON.stringify(publishData, null, 2), 'utf-8');

console.log('✅ Publish data saved:', publishDataFile);
console.log('');
console.log('🤖 Claude Code can now use MCP tools to complete the publish.');
console.log('');

process.exit(0);
