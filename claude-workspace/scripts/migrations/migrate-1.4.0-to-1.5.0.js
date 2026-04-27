#!/usr/bin/env node

/**
 * Migration: 1.4.0 → 1.5.0
 * Purpose: Convert single-file task tracking to multi-file system
 */

const fs = require('fs');
const path = require('path');

console.log('🔄 Migration: 1.4.0 → 1.5.0');
console.log('   Task tracking: Single-file → Multi-file');
console.log('');

// Check if migration needed
if (!fs.existsSync('docs/tasks/dashboard.md')) {
  console.log('ℹ️  No docs/tasks/dashboard.md found, skipping migration');
  process.exit(0);
}

// Check if already migrated
if (fs.existsSync('docs/tasks/') && fs.readdirSync('docs/tasks/').length > 1) {
  console.log('ℹ️  Multi-file system already exists, skipping migration');
  process.exit(0);
}

// Check for .gitkeep only
const tasksDir = 'docs/tasks/';
if (fs.existsSync(tasksDir)) {
  const files = fs.readdirSync(tasksDir).filter(f => f !== '.gitkeep');
  if (files.length > 0) {
    console.log('ℹ️  Multi-file system already exists, skipping migration');
    process.exit(0);
  }
}

// Run migration
try {
  console.log('📦 Backing up docs/tasks/dashboard.md...');
  fs.copyFileSync('docs/tasks/dashboard.md', 'docs/tasks/dashboard.md.pre-migration');

  console.log('🔄 Running migration script...');

  // Check if migration script exists
  if (!fs.existsSync('scripts/migrate-tasks-to-multifile.js')) {
    console.log('ℹ️  Migration script not found, assuming new project setup');
    process.exit(0);
  }

  // Run the migration
  const { execSync } = require('child_process');
  execSync('node scripts/migrate-tasks-to-multifile.js', { stdio: 'inherit' });

  console.log('');
  console.log('✅ Migration complete');
  console.log('   Backup: docs/tasks/dashboard.md.pre-migration');
  console.log('   New structure: docs/tasks/*.md');
  console.log('');

} catch (error) {
  console.error('');
  console.error('❌ Migration failed:', error.message);
  console.error('   You can run manually: node scripts/migrate-tasks-to-multifile.js');
  console.error('');
  process.exit(1);
}
