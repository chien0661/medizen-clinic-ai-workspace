#!/usr/bin/env node

/**
 * SonarQube MCP Server
 * Provides SonarQube quality gate validation via Model Context Protocol
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { SonarQubeClient } from './lib/sonarqube-client.js';
import { QualityGateChecker } from './lib/quality-gate-checker.js';
import { ErrorHandler } from './lib/error-handler.js';

// SonarQube configuration from environment variables
const SONARQUBE_CONFIG = {
  baseUrl: process.env.SONARQUBE_URL || 'https://sonarqube.vissoft.vn',
  token: process.env.SONARQUBE_TOKEN,
  timeout: parseInt(process.env.SONARQUBE_TIMEOUT || '30000'),
};

// Validate configuration
if (!SONARQUBE_CONFIG.token) {
  console.error('ERROR: SONARQUBE_TOKEN environment variable is required');
  console.error('Please set: export SONARQUBE_TOKEN=your-token-here');
  process.exit(1);
}

class SonarQubeMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'sonarqube-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Initialize SonarQube client and checker
    this.client = new SonarQubeClient(SONARQUBE_CONFIG);
    this.checker = new QualityGateChecker(this.client, SONARQUBE_CONFIG.baseUrl);

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  setupErrorHandling() {
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', () => {
      console.error('Shutting down SonarQube MCP server...');
      process.exit(0);
    });
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'get_quality_gate',
          description: 'Get quality gate status for a SonarQube project. Returns the overall status (OK/WARN/ERROR) and individual conditions.',
          inputSchema: {
            type: 'object',
            properties: {
              projectKey: {
                type: 'string',
                description: 'SonarQube project key (e.g., "com.company:project")',
              },
              branch: {
                type: 'string',
                description: 'Branch name (optional, defaults to main branch)',
              },
            },
            required: ['projectKey'],
          },
        },
        {
          name: 'get_issues',
          description: 'Search for code quality issues in a SonarQube project. Filter by severity, type, or creation date.',
          inputSchema: {
            type: 'object',
            properties: {
              projectKey: {
                type: 'string',
                description: 'SonarQube project key',
              },
              branch: {
                type: 'string',
                description: 'Branch name (optional)',
              },
              severity: {
                type: 'string',
                description: 'Filter by severity: BLOCKER, CRITICAL, MAJOR, MINOR, INFO',
                enum: ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO'],
              },
              types: {
                type: 'string',
                description: 'Filter by type (comma-separated): BUG,VULNERABILITY,CODE_SMELL,SECURITY_HOTSPOT',
              },
              createdAfter: {
                type: 'string',
                description: 'Only issues created after this date (ISO 8601 format: 2024-01-01)',
              },
            },
            required: ['projectKey'],
          },
        },
        {
          name: 'get_metrics',
          description: 'Get code quality metrics for a SonarQube project (coverage, bugs, vulnerabilities, code smells, etc.)',
          inputSchema: {
            type: 'object',
            properties: {
              projectKey: {
                type: 'string',
                description: 'SonarQube project key',
              },
              branch: {
                type: 'string',
                description: 'Branch name (optional)',
              },
              metrics: {
                type: 'array',
                items: { type: 'string' },
                description: 'Specific metrics to retrieve (default: coverage, bugs, vulnerabilities, code_smells)',
              },
            },
            required: ['projectKey'],
          },
        },
        {
          name: 'validate_quality_gate',
          description: 'Validate if a project passes its quality gate. Returns detailed failure reasons if not passing. Used by commit-push-pr skill to enforce quality standards.',
          inputSchema: {
            type: 'object',
            properties: {
              projectKey: {
                type: 'string',
                description: 'SonarQube project key',
              },
              branch: {
                type: 'string',
                description: 'Branch name (optional)',
              },
            },
            required: ['projectKey'],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'get_quality_gate':
            return await this.handleGetQualityGate(args.projectKey, args.branch);
          case 'get_issues':
            return await this.handleGetIssues(args.projectKey, args.branch, {
              severity: args.severity,
              types: args.types,
              createdAfter: args.createdAfter,
            });
          case 'get_metrics':
            return await this.handleGetMetrics(args.projectKey, args.branch, args.metrics);
          case 'validate_quality_gate':
            return await this.handleValidateQualityGate(args.projectKey, args.branch);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        // Handle errors with fail-safe mode
        const sonarError = ErrorHandler.handle(error);
        return ErrorHandler.formatErrorResponse(sonarError);
      }
    });
  }

  async handleGetQualityGate(projectKey, branch) {
    const status = await this.client.getQualityGateStatus(projectKey, branch);

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(status, null, 2),
      }],
    };
  }

  async handleGetIssues(projectKey, branch, filters) {
    const result = await this.checker.getIssues(projectKey, branch, filters);

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
    };
  }

  async handleGetMetrics(projectKey, branch, metrics) {
    const result = await this.checker.getMetrics(projectKey, branch, metrics);

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
    };
  }

  async handleValidateQualityGate(projectKey, branch) {
    const result = await this.checker.validateQualityGate(projectKey, branch);

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
      isError: !result.passed,
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('SonarQube MCP server running on stdio');
    console.error(`Connected to: ${SONARQUBE_CONFIG.baseUrl}`);
  }
}

// Start the server
const server = new SonarQubeMCPServer();
server.run().catch(console.error);
