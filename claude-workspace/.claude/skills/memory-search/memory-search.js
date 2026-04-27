#!/usr/bin/env node

/**
 * Memory Search Skill
 *
 * Searches persistent memory for relevant observations.
 * Usage: /memory-search <query> [limit]
 */

const http = require('http');
const path = require('path');

// Configuration from environment
const WORKER_URL = process.env.WORKER_URL || 'http://10.10.100.22:37777';
const MEMORY_API_KEY = process.env.MEMORY_API_KEY;

// Parse command line arguments (supports: "query" --limit N --type T)
const args = process.argv.slice(2);
const projectName = path.basename(process.cwd());
let query = null;
let limit = 10;
let toolType = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--limit' && args[i + 1]) {
    limit = parseInt(args[++i]) || 10;
  } else if (args[i] === '--type' && args[i + 1]) {
    toolType = args[++i];
  } else if (!query) {
    query = args[i];
  } else if (!isNaN(parseInt(args[i]))) {
    limit = parseInt(args[i]);
  }
}

function printUsage() {
  console.log('Usage: /memory-search <query> [limit]');
  console.log('');
  console.log('Examples:');
  console.log('  /memory-search "SDK documentation"');
  console.log('  /memory-search "authentication" 5');
  console.log('  /memory-search "TASK-003"');
  process.exit(1);
}

function printError(message, details) {
  console.log('\n❌ Error: ' + message);
  if (details) {
    console.log(details);
  }
  console.log('');
  process.exit(1);
}

async function searchMemory(query, limit, project, type) {
  return new Promise((resolve, reject) => {
    const url = new URL(WORKER_URL + '/api/search');
    const body = {
      query: query,
      project: project,
      limit: limit,
      order: 'relevance'
    };
    if (type) body.type = type;
    const postData = JSON.stringify(body);

    const options = {
      hostname: url.hostname,
      port: url.port || 80,
      path: '/api/search',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'Authorization': 'Bearer ' + MEMORY_API_KEY
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(data));
          } catch (err) {
            reject(new Error('Invalid JSON response'));
          }
        } else {
          reject(new Error('Status: ' + res.statusCode + ' - ' + data));
        }
      });
    });

    req.on('error', (err) => {
      reject(new Error('Cannot reach server: ' + err.message));
    });

    req.write(postData);
    req.end();
  });
}

async function search() {
  // Validate arguments
  if (!query) {
    printUsage();
  }

  // Check API key
  if (!MEMORY_API_KEY) {
    printError(
      'MEMORY_API_KEY not configured',
      'Please ensure MEMORY_API_KEY is set in .claude/settings.local.json'
    );
  }

  console.log('\n🔍 Memory Search Results\n');
  console.log('Query: "' + query + '"');
  console.log('Project: ' + projectName);
  if (toolType) console.log('Type: ' + toolType);
  console.log('Limit: ' + limit);
  console.log('');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  try {
    const results = await searchMemory(query, limit, projectName, toolType);

    if (!results.results || results.results.length === 0) {
      console.log('⚠️  No results found for query: "' + query + '"\n');
      console.log('Try:');
      console.log('  - Using different keywords');
      console.log('  - Checking if content has been imported');
      console.log('  - Using /memory-import to add content\n');
      process.exit(0);
    }

    console.log('✅ Found ' + results.results.length + ' result(s)\n');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    // Display each result
    results.results.forEach((result, index) => {
      console.log('📄 Result ' + (index + 1) + ' of ' + results.results.length + '\n');
      console.log('ID: ' + result.id);
      console.log('Type: ' + result.type);
      console.log('Title: ' + result.title);
      console.log('Timestamp: ' + result.timestamp);

      if (result.relevance_score) {
        console.log('Relevance: ' + result.relevance_score.toFixed(2));
      }

      if (result.session_id) {
        console.log('Session: ' + result.session_id);
      }

      console.log('');

      // Show preview if available
      if (result.preview) {
        console.log('Preview:');
        console.log('  ' + result.preview.substring(0, 200) + '...');
        console.log('');
      }

      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    });

    console.log('💡 To get full details, Claude can use the MCP tool:');
    console.log('   get_observations([' + results.results.map(r => r.id).join(', ') + '])\n');
    console.log('   Or ask Claude about this topic - it will load automatically!\n');

  } catch (err) {
    printError('Search failed', err.message);
  }
}

// Run
search();
