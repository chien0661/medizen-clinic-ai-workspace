import initSqlJs, { Database as SqlJsDatabase } from 'sql.js';
import path from 'path';
import os from 'os';
import fs from 'fs';

export interface Session {
  id: number;
  claude_session_id: string;
  project_name: string;
  first_prompt: string | null;
  prompt_count: number;
  status: 'initialized' | 'active' | 'completed';
  created_at: string;
  completed_at: string | null;
}

export interface UserPrompt {
  id: number;
  session_id: number;
  prompt_number: number;
  prompt_text: string;
  created_at: string;
}

export interface Observation {
  id: number;
  session_id: number;
  tool_name: string;
  tool_input: string | null;
  tool_response: string | null;
  compressed_observation: string | null;
  created_at: string;
  project_name: string | null;
}

export interface SessionSummary {
  id: number;
  session_id: number;
  request: string | null;
  investigated: string | null;
  learned: string | null;
  completed: string | null;
  next_steps: string | null;
  created_at: string;
}

export class MemoryDatabase {
  private db!: SqlJsDatabase;
  private dbPath: string;
  private initialized: boolean = false;
  private initPromise: Promise<void>;

  constructor(dbPath?: string) {
    // Default to ~/.claude-mem/memory.db
    if (!dbPath) {
      const homeDir = os.homedir();
      const memDir = path.join(homeDir, '.claude-mem');

      // Ensure directory exists
      if (!fs.existsSync(memDir)) {
        fs.mkdirSync(memDir, { recursive: true });
      }

      this.dbPath = path.join(memDir, 'memory.db');
    } else {
      this.dbPath = dbPath;
    }

    // Initialize asynchronously
    this.initPromise = this.initialize();
  }

  private async initialize() {
    try {
      // Initialize sql.js
      const SQL = await initSqlJs();

      // Load existing database or create new
      if (fs.existsSync(this.dbPath)) {
        const buffer = fs.readFileSync(this.dbPath);
        this.db = new SQL.Database(buffer);
      } else {
        this.db = new SQL.Database();
      }

      this.initialized = true;
      this.initSchema();
    } catch (error) {
      console.error('[Database] Failed to initialize:', error);
      throw error;
    }
  }

  /**
   * Wait for database to be initialized
   */
  async ready(): Promise<void> {
    await this.initPromise;
  }

  private initSchema() {
    this.db.run(`
      CREATE TABLE IF NOT EXISTS sdk_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claude_session_id TEXT UNIQUE NOT NULL,
        project_name TEXT NOT NULL,
        first_prompt TEXT,
        prompt_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'initialized',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
      );
    `);

    this.db.run(`CREATE INDEX IF NOT EXISTS idx_sessions_project ON sdk_sessions(project_name);`);
    this.db.run(`CREATE INDEX IF NOT EXISTS idx_sessions_status ON sdk_sessions(status);`);
    this.db.run(`CREATE INDEX IF NOT EXISTS idx_sessions_created ON sdk_sessions(created_at DESC);`);

    this.db.run(`
      CREATE TABLE IF NOT EXISTS user_prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        prompt_number INTEGER NOT NULL,
        prompt_text TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sdk_sessions(id) ON DELETE CASCADE
      );
    `);

    this.db.run(`CREATE INDEX IF NOT EXISTS idx_prompts_session ON user_prompts(session_id);`);

    this.db.run(`
      CREATE TABLE IF NOT EXISTS observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        tool_name TEXT NOT NULL,
        tool_input TEXT,
        tool_response TEXT,
        compressed_observation TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sdk_sessions(id) ON DELETE CASCADE
      );
    `);

    this.db.run(`CREATE INDEX IF NOT EXISTS idx_observations_session ON observations(session_id);`);
    this.db.run(`CREATE INDEX IF NOT EXISTS idx_observations_tool ON observations(tool_name);`);
    this.db.run(`CREATE INDEX IF NOT EXISTS idx_observations_created ON observations(created_at DESC);`);

    // Migration: add project_name column to observations if missing
    this.migrateObservationsProjectName();

    this.db.run(`
      CREATE TABLE IF NOT EXISTS session_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL UNIQUE,
        request TEXT,
        investigated TEXT,
        learned TEXT,
        completed TEXT,
        next_steps TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sdk_sessions(id) ON DELETE CASCADE
      );
    `);

    this.setupFTS();
    this.save(); // Save schema creation
  }

  private migrateObservationsProjectName() {
    const tableInfo = this.db.exec(`PRAGMA table_info(observations)`);
    const columns = tableInfo.length > 0 ? tableInfo[0].values.map((row: any[]) => row[1]) : [];

    if (!columns.includes('project_name')) {
      console.log('[Database] Migrating: adding project_name column to observations');
      this.db.run(`ALTER TABLE observations ADD COLUMN project_name TEXT`);

      // Backfill from session's project_name
      this.db.run(`
        UPDATE observations SET project_name = (
          SELECT s.project_name FROM sdk_sessions s WHERE s.id = observations.session_id
        ) WHERE project_name IS NULL
      `);

      this.db.run(`CREATE INDEX IF NOT EXISTS idx_observations_project ON observations(project_name);`);
      this.save();
      console.log('[Database] Migration complete: project_name column added and backfilled');
    }
  }

  private setupFTS() {
    // FTS5 is not available in default sql.js build
    // We'll use simple LIKE-based search instead
    // Note: For production with large datasets, consider building sql.js with FTS5
    console.log('[Database] FTS5 not available, using LIKE-based search');
  }

  /**
   * Save database to disk
   */
  private save() {
    try {
      const data = this.db.export();
      fs.writeFileSync(this.dbPath, data);
    } catch (error) {
      console.error('[Database] Failed to save:', error);
    }
  }

  // Session Methods
  createSession(claudeSessionId: string, projectName: string, firstPrompt?: string): Session {
    // Check if session already exists
    const existing = this.getSessionByClaudeId(claudeSessionId);

    if (existing) {
      // Update existing session's project_name (don't change ID or delete observations)
      this.db.run(
        `UPDATE sdk_sessions SET project_name = ?, first_prompt = COALESCE(?, first_prompt) WHERE claude_session_id = ?`,
        [projectName, firstPrompt || null, claudeSessionId]
      );
    } else {
      // Insert new session
      this.db.run(
        `INSERT INTO sdk_sessions (claude_session_id, project_name, first_prompt) VALUES (?, ?, ?)`,
        [claudeSessionId, projectName, firstPrompt || null]
      );
    }

    this.save();
    return this.getSessionByClaudeId(claudeSessionId)!;
  }

  getSessionByClaudeId(claudeSessionId: string): Session | undefined {
    const result = this.db.exec(`SELECT * FROM sdk_sessions WHERE claude_session_id = ?`, [claudeSessionId]);
    return this.rowToSession(result);
  }

  getSessionById(sessionId: number): Session | undefined {
    const result = this.db.exec(`SELECT * FROM sdk_sessions WHERE id = ?`, [sessionId]);
    return this.rowToSession(result);
  }

  updateSessionStatus(sessionId: number, status: 'active' | 'completed') {
    if (status === 'completed') {
      this.db.run(
        `UPDATE sdk_sessions SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?`,
        [status, sessionId]
      );
    } else {
      this.db.run(`UPDATE sdk_sessions SET status = ? WHERE id = ?`, [status, sessionId]);
    }
    this.save();
  }

  incrementPromptCount(sessionId: number) {
    this.db.run(`UPDATE sdk_sessions SET prompt_count = prompt_count + 1 WHERE id = ?`, [sessionId]);
    this.save();
  }

  getRecentSessions(projectName: string, limit: number = 10): Session[] {
    const result = this.db.exec(
      `SELECT * FROM sdk_sessions WHERE project_name = ? ORDER BY created_at DESC LIMIT ?`,
      [projectName, limit]
    );
    return this.rowsToSessions(result);
  }

  saveUserPrompt(sessionId: number, promptNumber: number, promptText: string): UserPrompt {
    this.db.run(
      `INSERT INTO user_prompts (session_id, prompt_number, prompt_text) VALUES (?, ?, ?)`,
      [sessionId, promptNumber, promptText]
    );
    this.save();

    const result = this.db.exec(`SELECT * FROM user_prompts WHERE session_id = ? AND prompt_number = ?`, [
      sessionId,
      promptNumber,
    ]);
    return this.rowToUserPrompt(result)!;
  }

  saveObservation(sessionId: number, toolName: string, toolInput?: string, toolResponse?: string, projectName?: string): Observation {
    this.db.run(
      `INSERT INTO observations (session_id, tool_name, tool_input, tool_response, project_name) VALUES (?, ?, ?, ?, ?)`,
      [sessionId, toolName, toolInput || null, toolResponse || null, projectName || null]
    );
    this.save();

    const result = this.db.exec(
      `SELECT * FROM observations WHERE session_id = ? ORDER BY id DESC LIMIT 1`,
      [sessionId]
    );
    return this.rowToObservation(result)!;
  }

  updateObservationCompression(observationId: number, compressedObservation: string) {
    this.db.run(`UPDATE observations SET compressed_observation = ? WHERE id = ?`, [
      compressedObservation,
      observationId,
    ]);
    this.save();
  }

  getObservationById(observationId: number): Observation | undefined {
    const result = this.db.exec(`SELECT * FROM observations WHERE id = ?`, [observationId]);
    return this.rowToObservation(result);
  }

  getObservationsBySession(sessionId: number): Observation[] {
    const result = this.db.exec(`SELECT * FROM observations WHERE session_id = ? ORDER BY created_at ASC`, [
      sessionId,
    ]);
    return this.rowsToObservations(result);
  }

  getPendingObservations(limit: number = 10): Observation[] {
    const result = this.db.exec(
      `SELECT * FROM observations WHERE compressed_observation IS NULL ORDER BY created_at ASC LIMIT ?`,
      [limit]
    );
    return this.rowsToObservations(result);
  }

  saveSummary(
    sessionId: number,
    request?: string,
    investigated?: string[],
    learned?: string[],
    completed?: string[],
    nextSteps?: string[]
  ) {
    this.db.run(
      `INSERT OR REPLACE INTO session_summaries
       (session_id, request, investigated, learned, completed, next_steps)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [
        sessionId,
        request || null,
        investigated ? JSON.stringify(investigated) : null,
        learned ? JSON.stringify(learned) : null,
        completed ? JSON.stringify(completed) : null,
        nextSteps ? JSON.stringify(nextSteps) : null,
      ]
    );
    this.save();
  }

  getSummary(sessionId: number): SessionSummary | undefined {
    const result = this.db.exec(`SELECT * FROM session_summaries WHERE session_id = ?`, [sessionId]);
    return this.rowToSummary(result);
  }

  searchObservations(query: string, projectName?: string, toolName?: string, limit: number = 20): Observation[] {
    // Simple LIKE-based search (FTS5 not available in default sql.js)
    let sql = `SELECT o.* FROM observations o`;
    const params: any[] = [];

    // Handle wildcard "*" as "match all" instead of literal search
    const isMatchAll = query === '*';

    // Build WHERE clause
    const whereClauses: string[] = [];

    if (!isMatchAll) {
      whereClauses.push(`(o.compressed_observation LIKE ? OR o.tool_input LIKE ? OR o.tool_response LIKE ?)`);
      const searchPattern = `%${query}%`;
      params.push(searchPattern, searchPattern, searchPattern);
    }

    if (projectName) {
      // Filter on per-observation project_name first; fall back to session-level for legacy rows with NULL
      whereClauses.push(`(o.project_name = ? OR (o.project_name IS NULL AND o.session_id IN (SELECT id FROM sdk_sessions WHERE project_name = ?)))`);
      params.push(projectName, projectName);
    }

    if (toolName) {
      whereClauses.push(`o.tool_name = ?`);
      params.push(toolName);
    }

    if (whereClauses.length > 0) {
      sql += ` WHERE ` + whereClauses.join(' AND ');
    }

    sql += ` ORDER BY o.created_at DESC LIMIT ?`;
    params.push(limit);

    const result = this.db.exec(sql, params);
    return this.rowsToObservations(result);
  }

  clearObservations(projectName: string): number {
    // Count observations to be deleted (per-observation project_name OR session-level fallback)
    const countResult = this.db.exec(
      `SELECT COUNT(*) FROM observations WHERE project_name = ? OR (project_name IS NULL AND session_id IN (SELECT id FROM sdk_sessions WHERE project_name = ?))`,
      [projectName, projectName]
    );
    const count = countResult.length > 0 ? countResult[0].values[0][0] as number : 0;

    // Delete observations
    this.db.run(
      `DELETE FROM observations WHERE project_name = ? OR (project_name IS NULL AND session_id IN (SELECT id FROM sdk_sessions WHERE project_name = ?))`,
      [projectName, projectName]
    );

    // Delete sessions that no longer have observations
    this.db.run(
      `DELETE FROM sdk_sessions WHERE project_name = ? AND id NOT IN (SELECT DISTINCT session_id FROM observations)`,
      [projectName]
    );

    // Clean up orphaned summaries
    this.db.run(
      `DELETE FROM session_summaries WHERE session_id NOT IN (SELECT id FROM sdk_sessions)`
    );

    this.save();
    return count;
  }

  close() {
    if (this.db) {
      this.save();
      this.db.close();
    }
  }

  // Helper methods to convert sql.js results to objects
  private rowToSession(result: any[]): Session | undefined {
    if (!result || result.length === 0 || !result[0].values || result[0].values.length === 0) {
      return undefined;
    }
    const row = result[0];
    const values = row.values[0];
    return {
      id: values[0],
      claude_session_id: values[1],
      project_name: values[2],
      first_prompt: values[3],
      prompt_count: values[4],
      status: values[5],
      created_at: values[6],
      completed_at: values[7],
    };
  }

  private rowsToSessions(result: any[]): Session[] {
    if (!result || result.length === 0 || !result[0].values) {
      return [];
    }
    const row = result[0];
    return row.values.map((values: any[]) => ({
      id: values[0],
      claude_session_id: values[1],
      project_name: values[2],
      first_prompt: values[3],
      prompt_count: values[4],
      status: values[5],
      created_at: values[6],
      completed_at: values[7],
    }));
  }

  private rowToUserPrompt(result: any[]): UserPrompt | undefined {
    if (!result || result.length === 0 || !result[0].values || result[0].values.length === 0) {
      return undefined;
    }
    const values = result[0].values[0];
    return {
      id: values[0],
      session_id: values[1],
      prompt_number: values[2],
      prompt_text: values[3],
      created_at: values[4],
    };
  }

  private rowToObservation(result: any[]): Observation | undefined {
    if (!result || result.length === 0 || !result[0].values || result[0].values.length === 0) {
      return undefined;
    }
    const values = result[0].values[0];
    return {
      id: values[0],
      session_id: values[1],
      tool_name: values[2],
      tool_input: values[3],
      tool_response: values[4],
      compressed_observation: values[5],
      created_at: values[6],
      project_name: values[7] ?? null,
    };
  }

  private rowsToObservations(result: any[]): Observation[] {
    if (!result || result.length === 0 || !result[0].values) {
      return [];
    }
    const row = result[0];
    return row.values.map((values: any[]) => ({
      id: values[0],
      session_id: values[1],
      tool_name: values[2],
      tool_input: values[3],
      tool_response: values[4],
      compressed_observation: values[5],
      created_at: values[6],
      project_name: values[7] ?? null,
    }));
  }

  private rowToSummary(result: any[]): SessionSummary | undefined {
    if (!result || result.length === 0 || !result[0].values || result[0].values.length === 0) {
      return undefined;
    }
    const values = result[0].values[0];
    return {
      id: values[0],
      session_id: values[1],
      request: values[2],
      investigated: values[3],
      learned: values[4],
      completed: values[5],
      next_steps: values[6],
      created_at: values[7],
    };
  }
}
