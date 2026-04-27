#!/usr/bin/env node

/**
 * Memory Export Skill
 *
 * Exports all memory observations to a markdown file for backup or review.
 * Usage: /memory-export [output_file] [project]
 */

const fs = require('fs');
const path = require('path');
const http = require('http');

// Configuration from environment
const WORKER_URL = process.env.WORKER_URL || 'http://localhost:37777';
const MEMORY_API_KEY = process.env.MEMORY_API_KEY;

// Parse command line arguments (supports: --file X or positional file arg)
const args = process.argv.slice(2);
const projectFilter = path.basename(process.cwd());
let outputFile = `docs/memory-export-${new Date().toISOString().split('T')[0]}.md`;

for (let i = 0; i < args.length; i++) {
  if ((args[i] === '--file' || args[i] === '-f') && args[i + 1]) {
    outputFile = args[++i];
  } else if (!args[i].startsWith('--')) {
    outputFile = args[i];
  }
}

function printError(message, details) {
  console.log('\n❌ Error: ' + message);
  if (details) {
    console.log(details);
  }
  console.log('');
  process.exit(1);
}

async function searchAllObservations(project) {
  return new Promise((resolve, reject) => {
    const url = new URL(WORKER_URL + '/api/search');
    const postData = JSON.stringify({
      query: '*',  // Get all
      project: project,
      limit: 1000,
      order: 'chronological'
    });

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
          reject(new Error('Status: ' + res.statusCode));
        }
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function getObservationDetails(ids) {
  return new Promise((resolve, reject) => {
    const url = new URL(WORKER_URL + '/api/observations');
    const postData = JSON.stringify({ ids: ids });

    const options = {
      hostname: url.hostname,
      port: url.port || 80,
      path: '/api/observations',
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
          reject(new Error('Status: ' + res.statusCode));
        }
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

function formatObservationAsMarkdown(obs) {
  let md = '';
  md += '### ' + (obs.tool_name || 'Unknown Tool') + '\n\n';
  md += '**Timestamp:** ' + (obs.timestamp || 'Unknown') + '\n';
  md += '**Session:** ' + (obs.session_id || 'Unknown') + '\n';
  if (obs.project_name) {
    md += '**Project:** ' + obs.project_name + '\n';
  }
  md += '\n';

  if (obs.tool_input) {
    md += '**Input:**\n```\n' + obs.tool_input + '\n```\n\n';
  }

  if (obs.tool_response) {
    const preview = obs.tool_response.length > 1000
      ? obs.tool_response.substring(0, 1000) + '\n...(truncated - ' + obs.tool_response.length + ' bytes total)...'
      : obs.tool_response;
    md += '**Output:**\n```\n' + preview + '\n```\n\n';
  }

  md += '---\n\n';
  return md;
}

async function exportMemory() {
  // Check API key
  if (!MEMORY_API_KEY) {
    printError(
      'MEMORY_API_KEY not configured',
      'Please ensure MEMORY_API_KEY is set in .claude/settings.local.json'
    );
  }

  console.log('\n📥 Exporting memory observations...\n');
  console.log('Project: ' + projectFilter);
  console.log('Output: ' + outputFile);
  console.log('Server: ' + WORKER_URL);
  console.log('');

  try {
    // Step 1: Search for all observations
    console.log('🔍 Searching for observations...');
    const searchResults = await searchAllObservations(projectFilter);

    if (!searchResults.results || searchResults.results.length === 0) {
      console.log('⚠️  No observations found for project: ' + projectFilter + '\n');
      process.exit(0);
    }

    console.log('✅ Found ' + searchResults.results.length + ' observations\n');

    // Step 2: Get full details for all observations
    console.log('📥 Fetching full observation details...');
    const ids = searchResults.results.map(r => r.id);
    const details = await getObservationDetails(ids);

    if (!details.observations || details.observations.length === 0) {
      printError('No observation details returned from server');
    }

    console.log('✅ Retrieved ' + details.observations.length + ' full observations\n');

    // Step 3: Format as markdown
    console.log('📝 Formatting as markdown...');

    let markdown = '# Memory Export\n\n';
    markdown += '**Project:** ' + projectFilter + '\n';
    markdown += '**Date:** ' + new Date().toISOString().split('T')[0] + '\n';
    markdown += '**Total Observations:** ' + details.observations.length + '\n';
    markdown += '**Server:** ' + WORKER_URL + '\n\n';
    markdown += '---\n\n';
    markdown += '## Observations\n\n';

    for (const obs of details.observations) {
      markdown += formatObservationAsMarkdown(obs);
    }

    // Step 4: Write to file
    console.log('💾 Writing to file: ' + outputFile + '\n');

    // Ensure directory exists
    const dir = path.dirname(outputFile);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(outputFile, markdown, 'utf-8');

    console.log('✅ Memory exported successfully!\n');
    console.log('Observations: ' + details.observations.length);
    console.log('File size: ' + Math.round(markdown.length / 1024) + ' KB');
    console.log('Location: ' + outputFile);
    console.log('');

  } catch (err) {
    printError('Failed to export memory', err.message);
  }
}

// Run
exportMemory();
