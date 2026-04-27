#!/usr/bin/env node

/**
 * MariaDB MCP Server
 * Provides database query capabilities via Model Context Protocol
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import mariadb from 'mariadb';

// Database configuration (from environment variables or config)
const DB_CONFIG = {
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '3306'),
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'miniapp_configuration',
  connectionLimit: 5,
};

// Create connection pool
const pool = mariadb.createPool(DB_CONFIG);

/**
 * Safely serialize data to JSON, converting BigInt values to strings
 * @param {any} data - Data to serialize
 * @returns {string} JSON string with BigInt values converted to strings
 */
function safeJSONStringify(data) {
  return JSON.stringify(data, (key, value) => {
    // Convert BigInt to string
    if (typeof value === 'bigint') {
      return value.toString();
    }
    return value;
  }, 2);
}

class MariaDBMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'mariadb-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  setupErrorHandling() {
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await pool.end();
      process.exit(0);
    });
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'query',
          description: 'Execute a SELECT query on the MariaDB database. Returns query results as JSON.',
          inputSchema: {
            type: 'object',
            properties: {
              sql: {
                type: 'string',
                description: 'The SQL SELECT query to execute',
              },
            },
            required: ['sql'],
          },
        },
        {
          name: 'execute',
          description: 'Execute an INSERT, UPDATE, or DELETE statement on the MariaDB database.',
          inputSchema: {
            type: 'object',
            properties: {
              sql: {
                type: 'string',
                description: 'The SQL statement to execute (INSERT, UPDATE, DELETE)',
              },
            },
            required: ['sql'],
          },
        },
        {
          name: 'schema',
          description: 'Get schema information for a table',
          inputSchema: {
            type: 'object',
            properties: {
              table: {
                type: 'string',
                description: 'Name of the table to describe',
              },
            },
            required: ['table'],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'query':
            return await this.handleQuery(args.sql);
          case 'execute':
            return await this.handleExecute(args.sql);
          case 'schema':
            return await this.handleSchema(args.table);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async handleQuery(sql) {
    let conn;
    try {
      // Validate it's a SELECT query
      const trimmedSQL = sql.trim().toUpperCase();
      if (!trimmedSQL.startsWith('SELECT') && !trimmedSQL.startsWith('SHOW') && !trimmedSQL.startsWith('DESCRIBE')) {
        throw new Error('Only SELECT, SHOW, and DESCRIBE queries are allowed with the query tool. Use execute tool for modifications.');
      }

      conn = await pool.getConnection();
      const rows = await conn.query(sql);

      return {
        content: [
          {
            type: 'text',
            text: safeJSONStringify(rows),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Query failed: ${error.message}`);
    } finally {
      if (conn) conn.release();
    }
  }

  async handleExecute(sql) {
    let conn;
    try {
      // Validate it's a modification query
      const trimmedSQL = sql.trim().toUpperCase();
      if (trimmedSQL.startsWith('SELECT') || trimmedSQL.startsWith('SHOW') || trimmedSQL.startsWith('DESCRIBE')) {
        throw new Error('Use query tool for SELECT statements');
      }

      if (trimmedSQL.startsWith('DROP') || trimmedSQL.startsWith('TRUNCATE')) {
        throw new Error('DROP and TRUNCATE operations are not allowed for safety');
      }

      conn = await pool.getConnection();
      const result = await conn.query(sql);

      return {
        content: [
          {
            type: 'text',
            text: safeJSONStringify({
              affectedRows: result.affectedRows,
              insertId: result.insertId,
              warningStatus: result.warningStatus,
              message: 'Statement executed successfully',
            }),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Execute failed: ${error.message}`);
    } finally {
      if (conn) conn.release();
    }
  }

  async handleSchema(table) {
    let conn;
    try {
      conn = await pool.getConnection();
      const columns = await conn.query(`DESCRIBE ${table}`);

      return {
        content: [
          {
            type: 'text',
            text: safeJSONStringify(columns),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Schema query failed: ${error.message}`);
    } finally {
      if (conn) conn.release();
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('MariaDB MCP server running on stdio');
  }
}

// Start the server
const server = new MariaDBMCPServer();
server.run().catch(console.error);
