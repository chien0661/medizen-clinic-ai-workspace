#!/usr/bin/env node

/**
 * Memory Setup Script
 *
 * One-time setup for the persistent memory system:
 * - Creates directory structure
 * - Installs dependencies
 * - Builds MCP server
 * - Initializes database
 * - Starts worker service
 * - Verifies everything works
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const WORKER_DIR = path.join(os.homedir(), '.claude-mem');
const LOG_DIR = path.join(WORKER_DIR, 'logs');
const MCP_SERVER_DIR = path.join(__dirname, '..', 'mcp-servers', 'claude-mem-server');
const WORKER_PORT = process.env.WORKER_PORT || 37777;

console.log('='.repeat(60));
console.log('Memory Setup - Persistent Memory for Claude Code');
console.log('='.repeat(60));
console.log('');

// Step 1: Create directory structure
console.log('[1/6] Creating directory structure...');
try {
  if (!fs.existsSync(WORKER_DIR)) {
    fs.mkdirSync(WORKER_DIR, { recursive: true });
    console.log(`  ✓ Created ${WORKER_DIR}`);
  } else {
    console.log(`  ✓ Directory exists: ${WORKER_DIR}`);
  }

  if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
    console.log(`  ✓ Created ${LOG_DIR}`);
  } else {
    console.log(`  ✓ Directory exists: ${LOG_DIR}`);
  }
} catch (error) {
  console.error(`  ✗ Failed to create directories: ${error.message}`);
  process.exit(1);
}

// Step 2: Check MCP server exists
console.log('\n[2/6] Checking MCP server...');
if (!fs.existsSync(MCP_SERVER_DIR)) {
  console.error(`  ✗ MCP server directory not found: ${MCP_SERVER_DIR}`);
  process.exit(1);
}
console.log(`  ✓ MCP server found`);

// Step 3: Install dependencies
console.log('\n[3/6] Installing dependencies...');
try {
  process.chdir(MCP_SERVER_DIR);

  // Check if node_modules exists
  const nodeModulesExists = fs.existsSync(path.join(MCP_SERVER_DIR, 'node_modules'));

  if (!nodeModulesExists) {
    console.log('  Installing npm packages (this may take a minute)...');
    execSync('npm install --ignore-scripts', { stdio: 'inherit' });
    console.log('  ✓ Dependencies installed');
  } else {
    console.log('  ✓ Dependencies already installed');
  }
} catch (error) {
  console.error(`  ✗ Failed to install dependencies: ${error.message}`);
  process.exit(1);
}

// Step 4: Build MCP server
console.log('\n[4/6] Building MCP server...');
try {
  const distExists = fs.existsSync(path.join(MCP_SERVER_DIR, 'dist'));

  if (!distExists) {
    console.log('  Compiling TypeScript...');
    execSync('npm run build', { stdio: 'inherit' });
    console.log('  ✓ Build successful');
  } else {
    console.log('  ✓ Already built');
  }
} catch (error) {
  console.error(`  ✗ Failed to build: ${error.message}`);
  process.exit(1);
}

// Step 5: Initialize database
console.log('\n[5/6] Initializing database...');
const dbPath = path.join(WORKER_DIR, 'memory.db');
if (!fs.existsSync(dbPath)) {
  console.log('  Database will be created on first worker start');
} else {
  console.log(`  ✓ Database exists: ${dbPath}`);
}

// Step 6: Start worker service
console.log('\n[6/6] Starting worker service...');
try {
  process.chdir(path.join(__dirname, '..'));
  execSync('node scripts/worker-service.js start', { stdio: 'inherit' });
  console.log('  ✓ Worker service started');
} catch (error) {
  console.error(`  ✗ Failed to start worker: ${error.message}`);
  process.exit(1);
}

// Final verification
console.log('');
console.log('='.repeat(60));
console.log('Setup Complete!');
console.log('='.repeat(60));
console.log('');
console.log('Memory system is now ready to use.');
console.log('');
console.log('Next steps:');
console.log('  • Restart Claude Code to activate memory hooks');
console.log('  • Memory will automatically capture tool usage');
console.log('  • Use /memory-search to search past work');
console.log('');
console.log('Useful commands:');
console.log('  node scripts/worker-service.js status   - Check worker status');
console.log('  node scripts/worker-service.js stop     - Stop worker');
console.log('  node scripts/worker-service.js restart  - Restart worker');
console.log('');
console.log(`Worker logs: ${LOG_DIR}`);
console.log(`Database: ${dbPath}`);
console.log(`Health check: http://localhost:${WORKER_PORT}/api/health`);
console.log('');
