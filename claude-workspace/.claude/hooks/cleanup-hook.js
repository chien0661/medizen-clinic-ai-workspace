#!/usr/bin/env node

/**
 * Cleanup Hook (SessionEnd)
 *
 * Marks the session as complete when it ends.
 * - Posts to worker to mark session complete
 * - Captures completion reason (exit, clear, logout)
 */

const WORKER_URL = process.env.WORKER_URL || 'http://localhost:37777';
const path = require('path');
const FETCH_TIMEOUT_MS = 5000;

function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(timeout));
}

async function cleanupSession() {
  try {
    // Get session ID from environment
    const claudeSessionId = process.env.CLAUDE_SESSION_ID || 'unknown';
    const projectName = path.basename(process.cwd());

    // Get completion reason from args if provided
    const reason = process.argv[2] || 'session_end';

    // Get session ID from worker
    const sessionResponse = await fetchWithTimeout(`${WORKER_URL}/api/sessions/${claudeSessionId}/init`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        claude_session_id: claudeSessionId,
        project_name: projectName
      })
    });

    if (!sessionResponse.ok) {
      console.error('[Memory] Failed to get session ID');
      process.exit(0);
    }

    const sessionData = await sessionResponse.json();

    // Mark session as complete
    await fetchWithTimeout(`${WORKER_URL}/api/sessions/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionData.session_id,
        reason: reason
      })
    });

    console.error('[Memory] Session marked as complete');
    process.exit(0);
  } catch (error) {
    console.error('[Memory] Error during cleanup:', error.message);
    process.exit(0); // Don't fail the session
  }
}

// Main execution
cleanupSession();
