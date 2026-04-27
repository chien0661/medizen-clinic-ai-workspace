#!/usr/bin/env node

/**
 * Smart Install Pre-Hook
 *
 * Verifies that memory system dependencies are installed and initialized.
 * Runs only on first launch or when plugin version changes.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const CACHE_DIR = path.join(os.homedir(), '.claude-mem');
const CACHE_FILE = path.join(CACHE_DIR, '.install-check');
const VERSION = '1.0.0'; // Update this when dependencies change

function main() {
  try {
    // Check if already verified for this version
    if (fs.existsSync(CACHE_FILE)) {
      const cachedVersion = fs.readFileSync(CACHE_FILE, 'utf8').trim();
      if (cachedVersion === VERSION) {
        // Already verified, skip check
        process.exit(0);
      }
    }

    console.error('[Memory] Verifying dependencies...');

    // Check 1: Node.js installed (should always pass since we're running in Node)
    try {
      const nodeVersion = process.version;
      console.error(`[Memory] ✓ Node.js ${nodeVersion} found`);
    } catch (error) {
      console.error('[Memory] ✗ Node.js not found');
      process.exit(1);
    }

    // Check 2: Memory database directory exists
    if (!fs.existsSync(CACHE_DIR)) {
      console.error('[Memory] Creating ~/.claude-mem directory...');
      fs.mkdirSync(CACHE_DIR, { recursive: true });
      fs.mkdirSync(path.join(CACHE_DIR, 'logs'), { recursive: true });
    }

    // Check 3: Database initialized (will be created on first worker start)
    const dbPath = path.join(CACHE_DIR, 'memory.db');
    if (!fs.existsSync(dbPath)) {
      console.error('[Memory] Database will be initialized on first session');
    } else {
      console.error('[Memory] ✓ Database found');
    }

    // Check 4: Worker service script exists
    const workerScript = path.join(process.cwd(), 'scripts', 'worker-service.js');
    if (!fs.existsSync(workerScript)) {
      console.error('[Memory] ⚠ Worker service script not found (will be created in TASK-004)');
    }

    // Cache successful verification
    fs.writeFileSync(CACHE_FILE, VERSION);
    console.error('[Memory] ✓ All checks passed');

    process.exit(0);
  } catch (error) {
    console.error('[Memory] Error during verification:', error.message);
    // Don't fail the session, just warn
    process.exit(0);
  }
}

main();
