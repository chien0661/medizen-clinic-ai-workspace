#!/usr/bin/env node

/**
 * Save Hook (PostToolUse)
 *
 * Captures tool execution observations and sends them to the worker service.
 * - Reads tool use data from stdin
 * - Skips low-value tools
 * - Strips privacy tags
 * - Posts to worker API (fire-and-forget)
 */

const fs = require('fs');
const path = require('path');

const WORKER_URL = process.env.WORKER_URL || 'http://localhost:37777';
const DEBUG_LOG = path.join(process.cwd(), '.claude', 'hooks', 'save-hook-debug.log');

function debugLog(message) {
  const timestamp = new Date().toISOString();
  fs.appendFileSync(DEBUG_LOG, `[${timestamp}] ${message}\n`);
}

// Tools to skip (low value for memory)
// Cost optimization: Skip file/content search tools (Glob, Grep)
// These are low-value for memory as they're just searches, not changes
const SKIP_TOOLS = [
  'TodoWrite',
  'AskUserQuestion',
  'EnterPlanMode',
  'ExitPlanMode',
  'TaskCreate',
  'TaskUpdate',
  'TaskList',
  'TaskGet',
  'Skill',
  'Glob',  // File pattern searches (low value)
  'Grep'   // Content searches (low value)
];

function stripPrivateTags(text) {
  if (!text) return text;
  return text.replace(/<private>[\s\S]*?<\/private>/g, '[REDACTED]');
}

function stripContextTags(text) {
  if (!text) return text;
  return text.replace(/<claude-mem-context>[\s\S]*?<\/claude-mem-context>/g, '');
}

function stripAllTags(text) {
  if (!text) return text;
  let cleaned = stripPrivateTags(text);
  cleaned = stripContextTags(cleaned);
  return cleaned;
}

/**
 * Extract the project name from tool input file paths.
 * Looks for paths like "D:\01. PROJECTS\05.Internal\bot-trade\..."
 * and extracts "bot-trade" as the project name.
 * Falls back to path.basename(process.cwd()) when no file path found.
 */
function extractProjectName(toolName, toolInput) {
  const fallback = path.basename(process.cwd());

  if (!toolInput) return fallback;

  try {
    const inputStr = typeof toolInput === 'string' ? toolInput : JSON.stringify(toolInput);

    // Parse JSON to extract known file path fields
    let pathCandidates = [];

    try {
      const parsed = JSON.parse(inputStr);

      // Read/Write/Edit tools use file_path
      if (parsed.file_path) pathCandidates.push(parsed.file_path);
      // Glob/Grep tools use path
      if (parsed.path) pathCandidates.push(parsed.path);
      // Bash tool uses command - extract quoted paths
      if (parsed.command) {
        // Match Windows paths in double quotes: "D:\01. PROJECTS\..."
        const quotedPaths = parsed.command.match(/"([A-Za-z]:\\[^"]+)"/g);
        if (quotedPaths) {
          pathCandidates.push(...quotedPaths.map(p => p.replace(/^"|"$/g, '')));
        }
        // Match unquoted Windows paths (no spaces): D:\01.PROJECTS\...
        const unquotedPaths = parsed.command.match(/[A-Za-z]:\\[\w.\-\\]+/g);
        if (unquotedPaths) {
          pathCandidates.push(...unquotedPaths);
        }
      }
    } catch (e) {
      // Not JSON, try to extract paths from raw string
      const quotedPaths = inputStr.match(/"([A-Za-z]:\\[^"]+)"/g);
      if (quotedPaths) {
        pathCandidates.push(...quotedPaths.map(p => p.replace(/^"|"$/g, '')));
      }
    }

    // Try to extract project name from each path candidate
    for (const candidate of pathCandidates) {
      // Normalize backslashes to forward slashes
      const normalized = candidate.replace(/\\/g, '/');
      // Match pattern: 01. PROJECTS/<category>/<project-name>
      const match = normalized.match(/01\.\s*PROJECTS\/[^/]+\/([^/]+)/i);
      if (match && match[1]) {
        return match[1];
      }
    }
  } catch (e) {
    // Ignore extraction errors, use fallback
  }

  return fallback;
}

async function readStdin() {
  return new Promise((resolve) => {
    const chunks = [];
    process.stdin.on('data', (chunk) => chunks.push(chunk));
    process.stdin.on('end', () => {
      resolve(Buffer.concat(chunks).toString());
    });
  });
}

async function saveObservation() {
  try {
    debugLog('=== Hook started ===');

    // Read tool use data from stdin
    const input = await readStdin();
    debugLog(`Input received: ${input.substring(0, 200)}...`);

    const toolUse = JSON.parse(input);
    debugLog(`Tool name: ${toolUse.tool_name}`);
    debugLog(`Raw tool use keys: ${Object.keys(toolUse).join(', ')}`);
    debugLog(`Has input: ${!!toolUse.input}, Has output: ${!!toolUse.output}`);
    debugLog(`Has params: ${!!toolUse.params}, Has result: ${!!toolUse.result}`);

    // Skip low-value tools
    if (SKIP_TOOLS.includes(toolUse.tool_name)) {
      debugLog(`Skipping tool: ${toolUse.tool_name}`);
      process.exit(0);
    }

    // Get session ID from environment
    const claudeSessionId = process.env.CLAUDE_SESSION_ID || 'unknown';
    const sessionProjectName = path.basename(process.cwd());

    // Extract per-observation project name from tool input file paths
    const rawToolInput = toolUse.tool_input || '';
    const observationProjectName = extractProjectName(toolUse.tool_name, rawToolInput);
    debugLog(`Session ID: ${claudeSessionId}, Session Project: ${sessionProjectName}, Observation Project: ${observationProjectName}`);

    // Strip privacy tags from tool input and output
    // Claude Code sends: tool_input and tool_response
    const rawInput = toolUse.tool_input || '';
    const rawOutput = toolUse.tool_response || '';
    debugLog(`Raw input type: ${typeof rawInput}, length: ${typeof rawInput === 'string' ? rawInput.length : JSON.stringify(rawInput).length}`);
    debugLog(`Raw output type: ${typeof rawOutput}, length: ${typeof rawOutput === 'string' ? rawOutput.length : JSON.stringify(rawOutput).length}`);

    const cleanInput = stripAllTags(typeof rawInput === 'string' ? rawInput : JSON.stringify(rawInput));
    const cleanOutput = stripAllTags(typeof rawOutput === 'string' ? rawOutput : JSON.stringify(rawOutput));

    // Prepare observation data
    const observation = {
      claude_session_id: claudeSessionId,
      project_name: sessionProjectName,
      observation_project_name: observationProjectName,
      tool_name: toolUse.tool_name,
      tool_input: cleanInput,
      tool_response: cleanOutput
    };

    // Get API key from environment
    const MEMORY_API_KEY = process.env.MEMORY_API_KEY;
    debugLog(`API Key: ${MEMORY_API_KEY ? MEMORY_API_KEY.substring(0, 20) + '...' : 'NOT SET'}`);
    debugLog(`Worker URL: ${WORKER_URL}`);

    // First, ensure session exists
    debugLog('Calling session init (first attempt)...');
    await fetch(`${WORKER_URL}/api/sessions/${claudeSessionId}/init`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${MEMORY_API_KEY}`
      },
      body: JSON.stringify({
        claude_session_id: claudeSessionId,
        project_name: sessionProjectName
      })
    }).catch((err) => {
      debugLog(`Session init error (first): ${err.message}`);
    }); // Ignore errors (session might already exist)

    // Get session ID from worker
    debugLog('Calling session init (second attempt)...');
    const sessionResponse = await fetch(`${WORKER_URL}/api/sessions/${claudeSessionId}/init`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${MEMORY_API_KEY}`
      },
      body: JSON.stringify({
        claude_session_id: claudeSessionId,
        project_name: sessionProjectName
      })
    });

    debugLog(`Session response status: ${sessionResponse.status}`);

    if (!sessionResponse.ok) {
      const errorText = await sessionResponse.text();
      debugLog(`Session init failed: ${errorText}`);
      console.error('[Memory] Failed to get session ID');
      process.exit(0);
    }

    const sessionData = await sessionResponse.json();
    debugLog(`Session data: ${JSON.stringify(sessionData)}`);

    // Save observation - WAIT for response to ensure it worked
    debugLog('Saving observation...');
    debugLog(`Observation data: ${JSON.stringify({
      session_id: sessionData.session_id,
      tool_name: toolUse.tool_name,
      tool_input_length: cleanInput ? cleanInput.length : 0,
      tool_response_length: cleanOutput ? cleanOutput.length : 0
    })}`);

    const obsResponse = await fetch(`${WORKER_URL}/api/sessions/observations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${MEMORY_API_KEY}`
      },
      body: JSON.stringify({
        session_id: sessionData.session_id,
        tool_name: toolUse.tool_name,
        tool_input: cleanInput || '',
        tool_response: cleanOutput || '',
        project_name: observationProjectName
      })
    });

    debugLog(`Observation save status: ${obsResponse.status}`);
    const obsText = await obsResponse.text();
    debugLog(`Observation save response: ${obsText}`);

    if (!obsResponse.ok) {
      debugLog(`⚠️ WARNING: Observation save failed!`);
    } else {
      debugLog(`✅ Observation saved successfully`);
    }

    debugLog('=== Hook completed successfully ===');
    process.exit(0);
  } catch (error) {
    debugLog(`=== Hook error: ${error.message} ===`);
    debugLog(`Error stack: ${error.stack}`);
    console.error('[Memory] Error saving observation:', error.message);
    process.exit(0); // Don't fail the session
  }
}

// Main execution
saveObservation();
