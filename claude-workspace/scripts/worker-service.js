#!/usr/bin/env node

/**
 * Worker Service Management Script
 *
 * Manages the Memory worker service lifecycle:
 * - start: Start the worker in background
 * - stop: Stop the running worker
 * - restart: Restart the worker
 * - status: Check if worker is running
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const WORKER_DIR = path.join(os.homedir(), '.claude-mem');
const LOG_DIR = path.join(WORKER_DIR, 'logs');
const PID_FILE = path.join(WORKER_DIR, 'worker.pid');
const WORKER_PORT = process.env.WORKER_PORT || 37777;
const WORKER_SCRIPT = path.join(__dirname, '..', 'mcp-servers', 'claude-mem-server', 'dist', 'services', 'worker.js');

// Ensure directories exist
function ensureDirectories() {
  if (!fs.existsSync(WORKER_DIR)) {
    fs.mkdirSync(WORKER_DIR, { recursive: true });
  }
  if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
  }
}

// Check if worker is running
async function checkWorkerHealth() {
  try {
    const response = await fetch(`http://localhost:${WORKER_PORT}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

// Get worker PID from file
function getWorkerPid() {
  if (fs.existsSync(PID_FILE)) {
    const pid = parseInt(fs.readFileSync(PID_FILE, 'utf8').trim());
    return isNaN(pid) ? null : pid;
  }
  return null;
}

// Check if process is running
function isProcessRunning(pid) {
  if (!pid) return false;

  try {
    // On Windows, use tasklist
    if (process.platform === 'win32') {
      const output = execSync(`tasklist /FI "PID eq ${pid}" /NH`, { encoding: 'utf8' });
      return output.includes(pid.toString());
    } else {
      // On Unix, send signal 0 to check if process exists
      process.kill(pid, 0);
      return true;
    }
  } catch {
    return false;
  }
}

// Start worker service
async function startWorker() {
  ensureDirectories();

  // Check if already running
  const existingPid = getWorkerPid();
  if (existingPid && isProcessRunning(existingPid)) {
    console.log(`[Worker] Already running (PID ${existingPid})`);
    return;
  }

  // Check if worker script exists
  if (!fs.existsSync(WORKER_SCRIPT)) {
    console.error(`[Worker] Worker script not found: ${WORKER_SCRIPT}`);
    console.error('[Worker] Please build the MCP server first: cd mcp-servers/claude-mem-server && npm run build');
    process.exit(1);
  }

  // Create log file
  const date = new Date().toISOString().split('T')[0];
  const logFile = path.join(LOG_DIR, `worker-${date}.log`);

  console.log(`[Worker] Starting worker service...`);
  console.log(`[Worker] Log file: ${logFile}`);

  // Open log file synchronously to get file descriptor
  const logFd = fs.openSync(logFile, 'a');

  // Spawn worker process
  const worker = spawn('node', [WORKER_SCRIPT], {
    detached: true,
    stdio: ['ignore', logFd, logFd],
    env: {
      ...process.env,
      WORKER_PORT: WORKER_PORT.toString()
    }
  });

  // Close the file descriptor in parent process (child has its own copy)
  fs.closeSync(logFd);

  // Write PID file
  fs.writeFileSync(PID_FILE, worker.pid.toString());

  // Detach from parent process
  worker.unref();

  // Wait for worker to be ready
  console.log(`[Worker] Waiting for worker to be ready...`);
  for (let i = 0; i < 20; i++) {
    await new Promise(resolve => setTimeout(resolve, 500));
    if (await checkWorkerHealth()) {
      console.log(`[Worker] ✓ Worker service started successfully (PID ${worker.pid})`);
      console.log(`[Worker] Health check: http://localhost:${WORKER_PORT}/api/health`);
      return;
    }
  }

  console.error(`[Worker] ⚠ Worker started but health check failed. Check logs: ${logFile}`);
}

// Stop worker service
function stopWorker() {
  const pid = getWorkerPid();

  if (!pid) {
    console.log('[Worker] No PID file found. Worker not running.');
    return;
  }

  if (!isProcessRunning(pid)) {
    console.log(`[Worker] Process ${pid} not running. Cleaning up PID file.`);
    fs.unlinkSync(PID_FILE);
    return;
  }

  console.log(`[Worker] Stopping worker (PID ${pid})...`);

  try {
    if (process.platform === 'win32') {
      // On Windows, use taskkill
      execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' });
    } else {
      // On Unix, send SIGTERM
      process.kill(pid, 'SIGTERM');
    }

    // Wait a bit for graceful shutdown
    setTimeout(() => {
      if (isProcessRunning(pid)) {
        console.log('[Worker] Forcing shutdown...');
        try {
          if (process.platform === 'win32') {
            execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' });
          } else {
            process.kill(pid, 'SIGKILL');
          }
        } catch (e) {
          // Process might already be dead
        }
      }

      if (fs.existsSync(PID_FILE)) {
        fs.unlinkSync(PID_FILE);
      }

      console.log('[Worker] ✓ Worker stopped');
    }, 2000);
  } catch (error) {
    console.error('[Worker] Error stopping worker:', error.message);
  }
}

// Restart worker service
async function restartWorker() {
  console.log('[Worker] Restarting worker service...');
  stopWorker();
  await new Promise(resolve => setTimeout(resolve, 3000));
  await startWorker();
}

// Check worker status
async function checkStatus() {
  const pid = getWorkerPid();

  if (!pid) {
    console.log('[Worker] Status: Not running (no PID file)');
    return;
  }

  if (!isProcessRunning(pid)) {
    console.log(`[Worker] Status: Not running (PID ${pid} not found)`);
    console.log('[Worker] Cleaning up stale PID file...');
    fs.unlinkSync(PID_FILE);
    return;
  }

  const healthy = await checkWorkerHealth();
  if (healthy) {
    console.log(`[Worker] Status: Running (PID ${pid})`);
    console.log(`[Worker] Health check: ✓ OK`);
    console.log(`[Worker] Port: ${WORKER_PORT}`);
  } else {
    console.log(`[Worker] Status: Running (PID ${pid}) but health check failed`);
    console.log(`[Worker] Health check: ✗ FAIL`);
    const date = new Date().toISOString().split('T')[0];
    const logFile = path.join(LOG_DIR, `worker-${date}.log`);
    console.log(`[Worker] Check logs: ${logFile}`);
  }
}

// Main execution
const command = process.argv[2];

(async () => {
  switch (command) {
    case 'start':
      await startWorker();
      break;
    case 'stop':
      stopWorker();
      break;
    case 'restart':
      await restartWorker();
      break;
    case 'status':
      await checkStatus();
      break;
    default:
      console.log('Usage: node worker-service.js [start|stop|restart|status]');
      console.log('');
      console.log('Commands:');
      console.log('  start    - Start the worker service in background');
      console.log('  stop     - Stop the running worker service');
      console.log('  restart  - Restart the worker service');
      console.log('  status   - Check if worker is running');
      console.log('');
      console.log('Environment variables:');
      console.log('  WORKER_PORT - Port for worker service (default: 37777)');
      process.exit(1);
  }
})();
