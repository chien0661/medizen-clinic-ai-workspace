#!/usr/bin/env node

/**
 * check-track-status.js
 *
 * Reads docs/tasks/dashboard.md and shows progress of the 5 parallel dev tracks.
 * Use this from any of the 5 launched terminals to see what your peers are doing.
 *
 * Usage:
 *   node scripts/check-track-status.js              # full report
 *   node scripts/check-track-status.js --track BE-A # just one track
 *   node scripts/check-track-status.js --watch      # refresh every 30s
 *   node scripts/check-track-status.js --next       # show next runnable task per track
 */

const fs = require('fs');
const path = require('path');

const TRACKS = {
  'BE-A': {
    title: 'Core Pipeline',
    queue: ['TASK-001', 'TASK-002', 'TASK-003', 'TASK-004', 'TASK-005', 'TASK-007', 'TASK-009'],
  },
  'BE-B': {
    title: 'Inventory & Billing',
    queue: ['TASK-006', 'TASK-012', 'TASK-011', 'TASK-013'],
  },
  'BE-C': {
    title: 'Operations',
    queue: ['TASK-008', 'TASK-010', 'TASK-014', 'TASK-015'],
  },
  'FE-1': {
    title: 'Clinical UI',
    queue: ['TASK-016', 'TASK-017', 'TASK-018', 'TASK-019', 'TASK-024'],
  },
  'FE-2': {
    title: 'Support UI',
    queue: ['TASK-020', 'TASK-021', 'TASK-022', 'TASK-023'],
  },
};

const STATUS_ORDER = ['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'IN_TESTING', 'DOCUMENTING', 'DONE'];
const ACTIVE_STATUSES = new Set(['IN_PROGRESS', 'IN_REVIEW', 'IN_TESTING', 'DOCUMENTING']);

const COLOR = {
  reset: '\x1b[0m',
  bold:  '\x1b[1m',
  dim:   '\x1b[2m',
  red:   '\x1b[31m',
  green: '\x1b[32m',
  yellow:'\x1b[33m',
  blue:  '\x1b[34m',
  magenta:'\x1b[35m',
  cyan:  '\x1b[36m',
  gray:  '\x1b[90m',
};

const STATUS_COLOR = {
  TODO:        COLOR.gray,
  IN_PROGRESS: COLOR.cyan,
  IN_REVIEW:   COLOR.blue,
  IN_TESTING:  COLOR.magenta,
  DOCUMENTING: COLOR.yellow,
  DONE:        COLOR.green,
  UNKNOWN:     COLOR.red,
};

const dashboardPath = path.join(__dirname, '..', 'docs', 'tasks', 'dashboard.md');

function loadStatuses() {
  const content = fs.readFileSync(dashboardPath, 'utf8');
  const statuses = {};

  // Match lines like:
  //   | 0-1 | [TASK-001](TASK-001/task.md) | Foundation ... | High | DOCUMENTING | — |
  // Capture TASK ID and the 5th pipe-separated cell (status)
  const lineRegex = /\[(TASK-\d{3})\]\([^)]+\)[^|]*\|[^|]*\|[^|]*\|\s*([A-Z_]+)\s*\|/g;
  let m;
  while ((m = lineRegex.exec(content)) !== null) {
    statuses[m[1]] = m[2].trim();
  }

  // Also grab blockers from the last column for next-task computation
  const blockerRegex = /\[(TASK-\d{3})\]\([^)]+\)[^|]*\|[^|]*\|[^|]*\|\s*[A-Z_]+\s*\|\s*([^|]+)\|/g;
  const blockers = {};
  while ((m = blockerRegex.exec(content)) !== null) {
    const raw = m[2].trim();
    if (!raw || raw === '—' || raw === '-') {
      blockers[m[1]] = [];
    } else if (/^ALL/i.test(raw)) {
      blockers[m[1]] = ['ALL'];
    } else {
      blockers[m[1]] = (raw.match(/TASK-\d{3}|\d{3}/g) || [])
        .map(t => t.startsWith('TASK-') ? t : `TASK-${t}`);
    }
  }

  return { statuses, blockers };
}

function statusBadge(status) {
  const c = STATUS_COLOR[status] || STATUS_COLOR.UNKNOWN;
  return `${c}${status.padEnd(11)}${COLOR.reset}`;
}

function nextRunnable(track, statuses, blockers) {
  for (const taskId of track.queue) {
    const status = statuses[taskId] || 'UNKNOWN';
    if (status === 'DONE') continue;
    if (status !== 'TODO') {
      // Already in progress somewhere — keep waiting on it
      return { taskId, status, blocked: false, reason: 'in flight' };
    }
    const deps = blockers[taskId] || [];
    if (deps.includes('ALL')) {
      const allDone = Object.values(statuses).every(s => s === 'DONE');
      if (allDone) return { taskId, status, blocked: false };
      return { taskId, status, blocked: true, reason: 'waits on ALL tasks' };
    }
    const blocking = deps.filter(d => statuses[d] !== 'DONE');
    if (blocking.length === 0) {
      return { taskId, status, blocked: false };
    }
    return { taskId, status, blocked: true, reason: `blocked by ${blocking.join(', ')}` };
  }
  return null;
}

function renderTrack(name, track, statuses, blockers, opts = {}) {
  const lines = [];
  const counts = { TODO: 0, ACTIVE: 0, DONE: 0 };
  for (const t of track.queue) {
    const s = statuses[t] || 'UNKNOWN';
    if (s === 'DONE') counts.DONE++;
    else if (ACTIVE_STATUSES.has(s)) counts.ACTIVE++;
    else counts.TODO++;
  }
  const pct = Math.round((counts.DONE / track.queue.length) * 100);
  const bar = '█'.repeat(Math.floor(pct / 5)).padEnd(20, '░');

  lines.push(`${COLOR.bold}[${name}]${COLOR.reset} ${track.title}  ${COLOR.dim}${bar} ${pct}%${COLOR.reset}`);
  lines.push(`        ${COLOR.green}${counts.DONE} done${COLOR.reset}  |  ${COLOR.cyan}${counts.ACTIVE} active${COLOR.reset}  |  ${COLOR.gray}${counts.TODO} todo${COLOR.reset}`);

  if (opts.detailed !== false) {
    for (const t of track.queue) {
      const s = statuses[t] || 'UNKNOWN';
      const dim = s === 'DONE' ? COLOR.dim : '';
      lines.push(`        ${dim}${t}  ${statusBadge(s)}${COLOR.reset}`);
    }
  }

  const next = nextRunnable(track, statuses, blockers);
  if (next) {
    if (next.blocked) {
      lines.push(`        ${COLOR.red}-> next: ${next.taskId} (${next.reason})${COLOR.reset}`);
    } else {
      lines.push(`        ${COLOR.green}-> next: ${next.taskId} READY${COLOR.reset}`);
    }
  } else {
    lines.push(`        ${COLOR.green}-> track complete${COLOR.reset}`);
  }

  return lines.join('\n');
}

function render(opts = {}) {
  const { statuses, blockers } = loadStatuses();
  const out = [];
  out.push('');
  out.push(`${COLOR.bold}${COLOR.cyan}=== Parallel Track Status ===${COLOR.reset}  ${COLOR.dim}${new Date().toLocaleString()}${COLOR.reset}`);
  out.push('');

  const tracksToShow = opts.track
    ? { [opts.track]: TRACKS[opts.track] }
    : TRACKS;

  for (const [name, track] of Object.entries(tracksToShow)) {
    if (!track) {
      out.push(`${COLOR.red}Unknown track: ${name}${COLOR.reset}`);
      continue;
    }
    out.push(renderTrack(name, track, statuses, blockers, { detailed: !opts.next }));
    out.push('');
  }

  if (opts.next) {
    out.push(`${COLOR.dim}Tip: rerun without --next for full task lists${COLOR.reset}`);
  }
  return out.join('\n');
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
const opts = {
  watch: args.includes('--watch'),
  next:  args.includes('--next'),
};
const trackArgIdx = args.indexOf('--track');
if (trackArgIdx >= 0) opts.track = args[trackArgIdx + 1];

if (opts.watch) {
  const tick = () => {
    process.stdout.write('\x1b[2J\x1b[H'); // clear screen
    process.stdout.write(render(opts));
    process.stdout.write(`\n${COLOR.dim}(refreshing every 30s — Ctrl+C to stop)${COLOR.reset}\n`);
  };
  tick();
  setInterval(tick, 30_000);
} else {
  console.log(render(opts));
}
