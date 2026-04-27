#!/usr/bin/env node

/**
 * Context Hook (SessionStart)
 *
 * Injects context from previous sessions when a new session starts.
 * - Health checks worker service
 * - Starts worker if not running
 * - Fetches context from last 10 sessions
 * - Outputs markdown wrapped in <claude-mem-context> tags
 */

const WORKER_URL = process.env.WORKER_URL || 'http://localhost:37777';
const path = require('path');
const FETCH_TIMEOUT_MS = 5000;

function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(timeout));
}

async function checkWorkerHealth() {
  try {
    const response = await fetchWithTimeout(`${WORKER_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

async function startWorker() {
  try {
    const { spawn } = require('child_process');
    const workerScript = path.join(process.cwd(), 'scripts', 'worker-service.js');

    // Check if script exists
    const fs = require('fs');
    if (!fs.existsSync(workerScript)) {
      console.error('[Memory] Worker service script not found. Skipping memory features.');
      return false;
    }

    // Start worker in background
    const isWindows = process.platform === 'win32';
    const worker = spawn('node', [workerScript, 'start'], {
      detached: !isWindows,
      stdio: 'ignore',
      ...(isWindows ? { shell: true } : {})
    });
    worker.unref();

    // Wait for worker to be ready (max 10 attempts)
    for (let i = 0; i < 10; i++) {
      await sleep(500);
      if (await checkWorkerHealth()) {
        console.error('[Memory] ✓ Worker service started');
        return true;
      }
    }

    console.error('[Memory] ⚠ Worker service failed to start. Memory features disabled.');
    return false;
  } catch (error) {
    console.error('[Memory] Error starting worker:', error.message);
    return false;
  }
}

async function injectContext() {
  try {
    // Check worker health
    let healthy = await checkWorkerHealth();

    if (!healthy) {
      console.error('[Memory] Worker not responding. Attempting to start...');
      healthy = await startWorker();

      if (!healthy) {
        // Worker failed to start, but don't fail the session
        // Just skip context injection
        return;
      }
    }

    // Get project name from current working directory
    const projectName = path.basename(process.cwd());

    // Fetch context from worker
    const response = await fetchWithTimeout(
      `${WORKER_URL}/api/context/inject?project=${encodeURIComponent(projectName)}`
    );

    if (!response.ok) {
      console.error('[Memory] Failed to fetch context:', response.statusText);
      return;
    }

    const data = await response.json();

    // Output context markdown (will be injected into Claude's context)
    console.log(data.markdown);
  } catch (error) {
    console.error('[Memory] Error injecting context:', error.message);
    // Don't fail the session, just skip context injection
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Main execution
injectContext().catch(error => {
  console.error('[Memory] Fatal error:', error);
  process.exit(0); // Don't fail the session
});
