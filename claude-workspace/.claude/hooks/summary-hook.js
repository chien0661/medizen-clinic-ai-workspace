#!/usr/bin/env node

/**
 * Summary Hook (Stop)
 *
 * Generates a session summary when the user pauses or stops asking questions.
 * - Reads transcript JSONL file
 * - Extracts last user and assistant messages
 * - Posts to worker to generate structured summary
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const WORKER_URL = process.env.WORKER_URL || 'http://localhost:37777';
const FETCH_TIMEOUT_MS = 5000;

function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(timeout));
}

async function generateSummary() {
  try {
    // Get session ID from environment
    const claudeSessionId = process.env.CLAUDE_SESSION_ID || 'unknown';
    const projectName = path.basename(process.cwd());

    // Find transcript file
    const claudeDir = path.join(os.homedir(), '.claude');
    const transcriptFile = path.join(claudeDir, 'sessions', `${claudeSessionId}.jsonl`);

    let lastUserMessage = '';
    let lastAssistantMessage = '';

    // Read transcript if it exists
    if (fs.existsSync(transcriptFile)) {
      const lines = fs.readFileSync(transcriptFile, 'utf8').split('\n').filter(l => l.trim());

      // Parse last messages
      for (let i = lines.length - 1; i >= 0 && (!lastUserMessage || !lastAssistantMessage); i--) {
        try {
          const entry = JSON.parse(lines[i]);
          if (entry.role === 'user' && !lastUserMessage) {
            lastUserMessage = entry.content;
          } else if (entry.role === 'assistant' && !lastAssistantMessage) {
            lastAssistantMessage = entry.content;
          }
        } catch (e) {
          // Skip invalid JSON lines
        }
      }
    }

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

    // Generate summary
    await fetchWithTimeout(`${WORKER_URL}/api/sessions/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionData.session_id,
        last_user_message: lastUserMessage,
        last_assistant_message: lastAssistantMessage
      })
    });

    console.error('[Memory] Session summary saved');
    process.exit(0);
  } catch (error) {
    console.error('[Memory] Error generating summary:', error.message);
    process.exit(0); // Don't fail the session
  }
}

// Main execution
generateSummary();
