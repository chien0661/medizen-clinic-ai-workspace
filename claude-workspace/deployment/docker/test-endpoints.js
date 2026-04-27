#!/usr/bin/env node
/**
 * Test Claude Memory Worker Endpoints
 * Tests all API endpoints to verify functionality
 */

const http = require('http');

const SERVER_URL = 'http://localhost:37777';
const API_KEY = '5b79cc30dbd9734882b3726020203d3316d6cd789ebed956be0a04b7fea3dbe4';

// Color codes
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const RESET = '\x1b[0m';

let testsPassed = 0;
let testsFailed = 0;

function log(message, color = RESET) {
  console.log(`${color}${message}${RESET}`);
}

function makeRequest(path, method = 'GET', body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, SERVER_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      }
    };

    if (body) {
      const bodyStr = JSON.stringify(body);
      options.headers['Content-Length'] = Buffer.byteLength(bodyStr);
    }

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve({ statusCode: res.statusCode, data: json });
        } catch (e) {
          resolve({ statusCode: res.statusCode, data: data });
        }
      });
    });

    req.on('error', reject);

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

async function test(name, testFn) {
  try {
    process.stdout.write(`Testing ${name}... `);
    await testFn();
    log('✓ PASS', GREEN);
    testsPassed++;
  } catch (error) {
    log(`✗ FAIL: ${error.message}`, RED);
    testsFailed++;
  }
}

async function runTests() {
  log('\n===========================================', YELLOW);
  log('  Claude Memory Worker - Endpoint Tests', YELLOW);
  log('===========================================\n', YELLOW);

  // Test 1: Health check
  await test('Health endpoint', async () => {
    const result = await makeRequest('/api/health');
    if (result.statusCode !== 200) {
      throw new Error(`Expected 200, got ${result.statusCode}`);
    }
    if (result.data.status !== 'ok') {
      throw new Error(`Expected status 'ok', got '${result.data.status}'`);
    }
  });

  // Test 2: Create session
  let sessionId;
  await test('Create session', async () => {
    const result = await makeRequest('/api/sessions', 'POST', {
      project: 'test-project',
      initial_prompt: 'Test initial prompt'
    });
    if (result.statusCode !== 200 && result.statusCode !== 201) {
      throw new Error(`Expected 200/201, got ${result.statusCode}`);
    }
    if (!result.data.session_id) {
      throw new Error('No session_id returned');
    }
    sessionId = result.data.session_id;
  });

  // Test 3: Add observation
  await test('Add observation', async () => {
    const result = await makeRequest('/api/sessions/observations', 'POST', {
      session_id: sessionId,
      tool_name: 'Read',
      input: { file_path: '/test/file.txt' },
      output: 'File contents here',
      timestamp: new Date().toISOString()
    });
    if (result.statusCode !== 200 && result.statusCode !== 201) {
      throw new Error(`Expected 200/201, got ${result.statusCode}`);
    }
  });

  // Test 4: Search (empty results expected for new DB)
  await test('Search endpoint', async () => {
    const result = await makeRequest('/api/search', 'POST', {
      query: 'test',
      project: 'test-project'
    });
    if (result.statusCode !== 200) {
      throw new Error(`Expected 200, got ${result.statusCode}`);
    }
    if (!result.data.results) {
      throw new Error('No results array returned');
    }
  });

  // Test 5: Timeline
  await test('Timeline endpoint', async () => {
    const result = await makeRequest('/api/timeline', 'POST', {
      session_id: sessionId
    });
    if (result.statusCode !== 200) {
      throw new Error(`Expected 200, got ${result.statusCode}`);
    }
  });

  // Test 6: Get observations
  await test('Get observations endpoint', async () => {
    const result = await makeRequest('/api/observations', 'POST', {
      observation_ids: [1]
    });
    if (result.statusCode !== 200) {
      throw new Error(`Expected 200, got ${result.statusCode}`);
    }
  });

  // Test 7: Context injection
  await test('Context injection endpoint', async () => {
    const result = await makeRequest('/api/context/inject?project=test-project', 'GET');
    if (result.statusCode !== 200) {
      throw new Error(`Expected 200, got ${result.statusCode}`);
    }
  });

  // Test 8: Complete session
  await test('Complete session', async () => {
    const result = await makeRequest('/api/sessions/complete', 'POST', {
      session_id: sessionId,
      reason: 'test_complete'
    });
    if (result.statusCode !== 200) {
      throw new Error(`Expected 200, got ${result.statusCode}`);
    }
  });

  // Summary
  log('\n===========================================', YELLOW);
  log(`  Test Results`, YELLOW);
  log('===========================================', YELLOW);
  log(`✓ Passed: ${testsPassed}`, GREEN);
  if (testsFailed > 0) {
    log(`✗ Failed: ${testsFailed}`, RED);
  }
  log(`  Total:  ${testsPassed + testsFailed}\n`, RESET);

  if (testsFailed === 0) {
    log('🎉 All tests passed!', GREEN);
    process.exit(0);
  } else {
    log('❌ Some tests failed', RED);
    process.exit(1);
  }
}

runTests().catch(error => {
  log(`\n❌ Test suite failed: ${error.message}`, RED);
  process.exit(1);
});
