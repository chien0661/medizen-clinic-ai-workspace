#!/usr/bin/env node

/**
 * Test script to verify SonarQube MCP server connectivity
 */

import { SonarQubeClient } from './lib/sonarqube-client.js';
import { QualityGateChecker } from './lib/quality-gate-checker.js';
import { ErrorHandler } from './lib/error-handler.js';

const SONARQUBE_CONFIG = {
  baseUrl: process.env.SONARQUBE_URL || 'https://sonarqube.vissoft.vn',
  token: process.env.SONARQUBE_TOKEN,
  timeout: 30000,
};

console.log('🧪 SonarQube MCP Server - Connection Test\n');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

// Check token
if (!SONARQUBE_CONFIG.token) {
  console.error('❌ ERROR: SONARQUBE_TOKEN environment variable is required');
  console.error('Please set: export SONARQUBE_TOKEN=your-token-here');
  process.exit(1);
}

console.log(`📍 Server: ${SONARQUBE_CONFIG.baseUrl}`);
console.log(`🔑 Token: ${SONARQUBE_CONFIG.token.substring(0, 10)}... (${SONARQUBE_CONFIG.token.length} chars)`);
console.log();

async function testConnection() {
  const client = new SonarQubeClient(SONARQUBE_CONFIG);
  const checker = new QualityGateChecker(client, SONARQUBE_CONFIG.baseUrl);

  console.log('Test 1: API Connectivity');
  console.log('─────────────────────────────────────────');

  try {
    // Test basic API call - get system status or projects
    const response = await client.request('/api/projects/search', { ps: 1 });
    console.log('✅ API is reachable');
    console.log(`✅ Authentication successful`);
    console.log(`📊 Found ${response.paging?.total || 0} project(s) in SonarQube`);

    if (response.components && response.components.length > 0) {
      console.log(`\n📋 Sample project: ${response.components[0].key}`);
    }
  } catch (error) {
    const sonarError = ErrorHandler.handle(error);
    console.error(`❌ Connection failed: ${sonarError.message}`);
    console.error(`   Error code: ${sonarError.code}`);
    if (sonarError.details && sonarError.details.guidance) {
      console.error(`\n💡 Guidance:`);
      sonarError.details.guidance.forEach((g, i) => {
        console.error(`   ${i + 1}. ${g}`);
      });
    }
    process.exit(1);
  }

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('✅ All tests passed!');
  console.log('\n🎉 SonarQube MCP server is ready to use!');
  console.log('\nNext steps:');
  console.log('1. Update PROJECT.md with your project key');
  console.log('2. Use /commit-push-pr to test quality gate enforcement');
  console.log('3. Or call MCP tools directly:');
  console.log('   - mcp__sonarqube__validate_quality_gate');
  console.log('   - mcp__sonarqube__get_issues');
  console.log('   - mcp__sonarqube__get_metrics');
}

testConnection().catch((error) => {
  console.error('\n❌ Unexpected error:', error.message);
  console.error(error.stack);
  process.exit(1);
});
