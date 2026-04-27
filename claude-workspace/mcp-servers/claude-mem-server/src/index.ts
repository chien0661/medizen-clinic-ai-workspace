#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

const WORKER_URL = process.env.WORKER_URL || 'http://localhost:37777';

// Endpoint mapping: MCP tool name → Worker API endpoint
const ENDPOINT_MAP: Record<string, string> = {
  'search': '/api/search',
  'timeline': '/api/timeline',
  'get_observations': '/api/observations'  // Tool name ≠ endpoint name
};

// MCP Server for Memory Search Tools
const server = new Server(
  {
    name: 'claude-mem-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'search',
        description: 'Search memory observations (Layer 1: Compact index). Returns ~50-100 tokens per result.',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Full-text search query'
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results (default: 20)',
              default: 20
            },
            project: {
              type: 'string',
              description: 'Filter by project name'
            },
            type: {
              type: 'string',
              description: 'Filter by tool type (e.g., Read, Write, Bash)'
            },
            order: {
              type: 'string',
              enum: ['relevance', 'chronological'],
              description: 'Sort order (default: relevance)',
              default: 'relevance'
            }
          },
          required: ['query']
        }
      },
      {
        name: 'timeline',
        description: 'Get chronological context around a specific observation (Layer 2: Timeline). Returns ~200-300 tokens per observation.',
        inputSchema: {
          type: 'object',
          properties: {
            anchor_id: {
              type: 'number',
              description: 'Observation ID to center timeline around'
            },
            query: {
              type: 'string',
              description: 'Search query to find anchor (if anchor_id not provided)'
            },
            before: {
              type: 'number',
              description: 'Number of observations before anchor (default: 5)',
              default: 5
            },
            after: {
              type: 'number',
              description: 'Number of observations after anchor (default: 5)',
              default: 5
            }
          }
        }
      },
      {
        name: 'get_observations',
        description: 'Get full observation details (Layer 3: Full details). Returns ~500-1,000 tokens per observation. Use ONLY after filtering through layers 1 and 2.',
        inputSchema: {
          type: 'object',
          properties: {
            ids: {
              type: 'array',
              items: { type: 'number' },
              description: 'List of observation IDs to fetch'
            }
          },
          required: ['ids']
        }
      },
      {
        name: '__IMPORTANT',
        description: 'ALWAYS READ THIS FIRST - Token-efficient workflow guide',
        inputSchema: {
          type: 'object',
          properties: {},
          additionalProperties: false
        }
      }
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === '__IMPORTANT') {
      return {
        content: [
          {
            type: 'text',
            text: `## Token-Efficient Memory Search Workflow

**CRITICAL: Always follow this three-layer pattern to minimize token usage**

### Layer 1: Search (Compact Index)
- Use \`search(query)\` to get a compact list of matching observations
- Returns ~50-100 tokens per result (ID, title, timestamp, type only)
- Filter to 3-5 most promising results

### Layer 2: Timeline (Chronological Context)
- Use \`timeline(anchor_id)\` for selected observation IDs from Layer 1
- Returns ~200-300 tokens per observation (includes context before/after)
- Understand what happened around that point in time

### Layer 3: Get Full Details
- Use \`get_observations(ids)\` ONLY for 1-3 final observations you need
- Returns ~500-1,000 tokens per observation (complete details)
- **NEVER fetch full details without filtering through layers 1 and 2 first**

### Token Savings
- Traditional RAG: Load all 50 observations upfront = 25K-50K tokens
- Three-layer approach: Search → Timeline → Details = 2K-5K tokens
- **Savings: 10x reduction in token consumption**

### Example Workflow
\`\`\`
1. search("authentication JWT login") → Get 20 result IDs
2. Pick 3 most relevant IDs
3. timeline(anchor_id=456) → See context around observation #456
4. get_observations([456, 457]) → Fetch full details for 2 observations only
\`\`\``,
          },
        ],
      };
    }

    // Forward other requests to worker API with endpoint mapping
    const endpoint = ENDPOINT_MAP[name];
    if (!endpoint) {
      throw new Error(`Unknown tool: ${name}`);
    }

    const response = await fetch(`${WORKER_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(args),
    });

    if (!response.ok) {
      throw new Error(`Worker API error: ${response.statusText}`);
    }

    const data = await response.json();

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('[MCP Server] Claude Memory MCP server running on stdio');
}

main().catch((error) => {
  console.error('[MCP Server] Fatal error:', error);
  process.exit(1);
});
