import express, { Request, Response } from 'express';
import cors from 'cors';
import { fileURLToPath } from 'url';
import { MemoryDatabase } from './database.js';
import { SDKAgent } from './sdk-agent.js';
import { SearchService } from './search.js';
import { stripPrivateTags } from '../utils/tag-stripping.js';

export class WorkerService {
  private app = express();
  private db: MemoryDatabase;
  private agent: SDKAgent;
  private search: SearchService;
  private port: number;

  constructor(port: number = 37777, dbPath?: string) {
    this.port = port;
    this.db = new MemoryDatabase(dbPath);
    this.agent = new SDKAgent(this.db);
    this.search = new SearchService(this.db);

    this.setupMiddleware();
    this.setupRoutes();
  }

  private setupMiddleware() {
    this.app.use(cors());
    this.app.use(express.json({ limit: '10mb' }));

    // Request logging
    this.app.use((req, res, next) => {
      const timestamp = new Date().toISOString();
      console.log(`[${timestamp}] ${req.method} ${req.url}`);
      next();
    });
  }

  private setupRoutes() {
    // Health check
    this.app.get('/api/health', (req: Request, res: Response) => {
      res.json({
        status: 'ok',
        uptime: process.uptime(),
        timestamp: new Date().toISOString()
      });
    });

    // Context injection
    this.app.get('/api/context/inject', async (req: Request, res: Response) => {
      try {
        const { project } = req.query;
        if (!project || typeof project !== 'string') {
          return res.status(400).json({ error: 'project parameter required' });
        }

        const markdown = await this.generateContextMarkdown(project);
        res.json({ markdown, project });
      } catch (error) {
        console.error('[Worker] Error generating context:', error);
        res.status(500).json({ error: 'Failed to generate context' });
      }
    });

    // Session initialization
    this.app.post('/api/sessions/:id/init', async (req: Request, res: Response) => {
      try {
        const { claude_session_id, project_name, first_prompt } = req.body;

        if (!claude_session_id || !project_name) {
          return res.status(400).json({ error: 'claude_session_id and project_name required' });
        }

        const session = this.db.createSession(claude_session_id, project_name, first_prompt);
        res.json({ session_id: session.id, status: 'initialized' });
      } catch (error) {
        console.error('[Worker] Error initializing session:', error);
        res.status(500).json({ error: 'Failed to initialize session' });
      }
    });

    // Save observation
    this.app.post('/api/sessions/observations', async (req: Request, res: Response) => {
      try {
        const { session_id, tool_name, tool_input, tool_response, project_name } = req.body;

        if (!session_id || !tool_name) {
          return res.status(400).json({ error: 'session_id and tool_name required' });
        }

        // Strip privacy tags
        const cleanInput = stripPrivateTags(tool_input);
        const cleanResponse = stripPrivateTags(tool_response);

        const observation = this.db.saveObservation(
          session_id,
          tool_name,
          cleanInput || undefined,
          cleanResponse || undefined,
          project_name || undefined
        );

        res.json({ observation_id: observation.id, queued: true });
      } catch (error) {
        console.error('[Worker] Error saving observation:', error);
        res.status(500).json({ error: 'Failed to save observation' });
      }
    });

    // Generate summary
    this.app.post('/api/sessions/summarize', async (req: Request, res: Response) => {
      try {
        const { session_id, last_user_message, last_assistant_message } = req.body;

        if (!session_id) {
          return res.status(400).json({ error: 'session_id required' });
        }

        // For now, create a simple summary
        // In production, this would use Claude Agent SDK to generate structured summary
        const request = last_user_message?.substring(0, 200) || 'No request captured';
        const investigated: string[] = [];
        const learned: string[] = [];
        const completed: string[] = [];
        const next_steps: string[] = [];

        this.db.saveSummary(session_id, request, investigated, learned, completed, next_steps);
        res.json({
          summary: { request, investigated, learned, completed, next_steps },
          status: 'saved'
        });
      } catch (error) {
        console.error('[Worker] Error generating summary:', error);
        res.status(500).json({ error: 'Failed to generate summary' });
      }
    });

    // Complete session
    this.app.post('/api/sessions/complete', async (req: Request, res: Response) => {
      try {
        const { session_id, reason } = req.body;

        if (!session_id) {
          return res.status(400).json({ error: 'session_id required' });
        }

        this.db.updateSessionStatus(session_id, 'completed');
        res.json({ status: 'completed', reason: reason || 'session_end' });
      } catch (error) {
        console.error('[Worker] Error completing session:', error);
        res.status(500).json({ error: 'Failed to complete session' });
      }
    });

    // Search (Layer 1)
    this.app.post('/api/search', async (req: Request, res: Response) => {
      try {
        const results = this.search.search(req.body);
        res.json({ results });
      } catch (error) {
        console.error('[Worker] Error searching:', error);
        res.status(500).json({ error: 'Search failed' });
      }
    });

    // Timeline (Layer 2)
    this.app.post('/api/timeline', async (req: Request, res: Response) => {
      try {
        const results = this.search.timeline(req.body);
        res.json(results);
      } catch (error) {
        console.error('[Worker] Error getting timeline:', error);
        res.status(500).json({ error: 'Timeline failed' });
      }
    });

    // Get observations (Layer 3)
    this.app.post('/api/observations', async (req: Request, res: Response) => {
      try {
        const observations = this.search.getObservations(req.body);
        res.json({ observations });
      } catch (error) {
        console.error('[Worker] Error getting observations:', error);
        res.status(500).json({ error: 'Failed to get observations' });
      }
    });

    // Clear observations for a project
    this.app.post('/api/observations/clear', async (req: Request, res: Response) => {
      try {
        const { project } = req.body;
        if (!project || typeof project !== 'string') {
          return res.status(400).json({ error: 'project parameter required' });
        }

        const deleted = this.db.clearObservations(project);
        console.log(`[Worker] Cleared ${deleted} observations for project: ${project}`);
        res.json({ success: true, deleted, project });
      } catch (error) {
        console.error('[Worker] Error clearing observations:', error);
        res.status(500).json({ error: 'Failed to clear observations' });
      }
    });
  }

  /**
   * Generate context markdown from recent sessions
   */
  private async generateContextMarkdown(project: string): Promise<string> {
    const sessions = this.db.getRecentSessions(project, 10);

    if (sessions.length === 0) {
      return '<claude-mem-context>\nNo previous sessions found for this project.\n</claude-mem-context>';
    }

    let markdown = '<claude-mem-context>\n';
    markdown += `## Previous Session Context (Last ${sessions.length} sessions)\n\n`;

    for (const session of sessions) {
      const summary = this.db.getSummary(session.id);
      if (summary) {
        const date = new Date(session.created_at).toLocaleDateString();
        markdown += `### Session ${date}: ${summary.request || 'Untitled'}\n`;

        if (summary.investigated) {
          const investigated = JSON.parse(summary.investigated);
          if (investigated.length > 0) {
            markdown += `- **Investigated**: ${investigated.join(', ')}\n`;
          }
        }

        if (summary.learned) {
          const learned = JSON.parse(summary.learned);
          if (learned.length > 0) {
            markdown += `- **Learned**: ${learned.join(', ')}\n`;
          }
        }

        if (summary.completed) {
          const completed = JSON.parse(summary.completed);
          if (completed.length > 0) {
            markdown += `- **Completed**: ${completed.join(', ')}\n`;
          }
        }

        if (summary.next_steps) {
          const nextSteps = JSON.parse(summary.next_steps);
          if (nextSteps.length > 0) {
            markdown += `- **Next**: ${nextSteps.join(', ')}\n`;
          }
        }

        markdown += '\n';
      }
    }

    markdown += '</claude-mem-context>';
    return markdown;
  }

  /**
   * Start the worker service
   */
  async start() {
    // Wait for database to be ready
    await this.db.ready();
    console.log('[Worker] Database initialized');

    // Start SDK Agent queue processor
    this.agent.start();

    // Start HTTP server
    return new Promise<void>((resolve) => {
      this.app.listen(this.port, '0.0.0.0', () => {
        console.log(`[Worker] Memory worker service listening on http://0.0.0.0:${this.port}`);
        resolve();
      });
    });
  }

  /**
   * Stop the worker service
   */
  async stop() {
    this.agent.stop();
    this.db.close();
    console.log('[Worker] Worker service stopped');
  }
}

// Start worker if run directly
const isMainModule = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];
if (isMainModule) {
  const port = parseInt(process.env.WORKER_PORT || '37777');
  const dbPath = process.env.MEMORY_DB_PATH;
  const worker = new WorkerService(port, dbPath);

  worker.start().catch((error) => {
    console.error('[Worker] Failed to start:', error);
    process.exit(1);
  });

  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log('\n[Worker] Shutting down gracefully...');
    await worker.stop();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    console.log('\n[Worker] Shutting down gracefully...');
    await worker.stop();
    process.exit(0);
  });
}
