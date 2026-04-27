#!/usr/bin/env node

/**
 * Memory Clear Skill
 *
 * Clears all memory observations for the current project.
 * ⚠️ WARNING: This action is PERMANENT and cannot be undone!
 *
 * Usage: /memory-clear [--confirm]
 */

const http = require('http');
const path = require('path');
const readline = require('readline');

// Configuration from environment
const WORKER_URL = process.env.WORKER_URL || 'http://10.10.100.22:37777';
const MEMORY_API_KEY = process.env.MEMORY_API_KEY;

// Parse command line arguments
const args = process.argv.slice(2);
const confirmed = args.includes('--confirm') || args.includes('-y');
const projectName = path.basename(process.cwd());

function printError(message, details) {
  console.log('\n❌ Error: ' + message);
  if (details) {
    console.log(details);
  }
  console.log('');
  process.exit(1);
}

async function clearMemory(project) {
  return new Promise((resolve, reject) => {
    const url = new URL(WORKER_URL + '/api/observations/clear');
    const postData = JSON.stringify({
      project: project
    });

    const options = {
      hostname: url.hostname,
      port: url.port || 80,
      path: '/api/observations/clear',
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
            resolve({ success: true });
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

async function getStats(project) {
  return new Promise((resolve, reject) => {
    const url = new URL(WORKER_URL + '/api/search');
    const postData = JSON.stringify({
      query: '*',
      project: project,
      limit: 1000
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
            const result = JSON.parse(data);
            resolve({ count: result.results ? result.results.length : 0 });
          } catch (err) {
            resolve({ count: 0 });
          }
        } else {
          resolve({ count: 0 });
        }
      });
    });

    req.on('error', () => {
      resolve({ count: 0 });
    });

    req.write(postData);
    req.end();
  });
}

async function promptUser(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.toLowerCase() === 'yes' || answer.toLowerCase() === 'y');
    });
  });
}

async function clear() {
  // Check API key
  if (!MEMORY_API_KEY) {
    printError(
      'MEMORY_API_KEY not configured',
      'Please ensure MEMORY_API_KEY is set in .claude/settings.local.json'
    );
  }

  console.log('\n⚠️  Memory Clear - PERMANENT DELETION\n');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  try {
    // Get current stats
    console.log('📊 Checking current memory...\n');
    const stats = await getStats(projectName);

    console.log('Project: ' + projectName);
    console.log('Server: ' + WORKER_URL);
    console.log('Total observations: ' + stats.count);
    console.log('');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    if (stats.count === 0) {
      console.log('✅ No observations found. Memory is already empty.\n');
      process.exit(0);
    }

    console.log('⚠️  WARNING: This will DELETE ALL ' + stats.count + ' observations!\n');
    console.log('This action is PERMANENT and CANNOT BE UNDONE.\n');
    console.log('Consider running /memory-export first to create a backup.\n');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    if (!confirmed) {
      const shouldProceed = await promptUser('Type "yes" to confirm deletion: ');

      if (!shouldProceed) {
        console.log('\n❌ Cancelled. No observations were deleted.\n');
        process.exit(0);
      }
    }

    console.log('\n🗑️  Clearing memory...\n');

    await clearMemory(projectName);

    console.log('✅ Memory cleared successfully!\n');
    console.log('Deleted: ' + stats.count + ' observations');
    console.log('Project: ' + projectName);
    console.log('');

  } catch (err) {
    printError('Failed to clear memory', err.message);
  }
}

// Run
clear();
