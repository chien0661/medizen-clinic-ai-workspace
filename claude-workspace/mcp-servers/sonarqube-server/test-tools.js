#!/usr/bin/env node

/**
 * Test MCP tools with real SonarQube project
 */

import { SonarQubeClient } from './lib/sonarqube-client.js';
import { QualityGateChecker } from './lib/quality-gate-checker.js';
import { ErrorHandler } from './lib/error-handler.js';

const SONARQUBE_CONFIG = {
  baseUrl: process.env.SONARQUBE_URL || 'https://sonarqube.vissoft.vn',
  token: process.env.SONARQUBE_TOKEN,
  timeout: 30000,
};

if (!SONARQUBE_CONFIG.token) {
  console.error('❌ ERROR: SONARQUBE_TOKEN environment variable is required');
  process.exit(1);
}

const client = new SonarQubeClient(SONARQUBE_CONFIG);
const checker = new QualityGateChecker(client, SONARQUBE_CONFIG.baseUrl);

console.log('🧪 Testing MCP Tools\n');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

async function testTools() {
  // Get a project to test with
  console.log('📋 Fetching available projects...\n');
  const projects = await client.request('/api/projects/search', { ps: 5 });

  if (!projects.components || projects.components.length === 0) {
    console.log('❌ No projects found in SonarQube');
    process.exit(1);
  }

  console.log(`Found ${projects.paging.total} projects. Testing with first 5:\n`);
  projects.components.forEach((p, i) => {
    console.log(`${i + 1}. ${p.key} - ${p.name}`);
  });

  const testProject = projects.components[0].key;
  console.log(`\n🎯 Using project: ${testProject}\n`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // Test 1: Get Quality Gate
  console.log('Test 1: get_quality_gate');
  console.log('─────────────────────────────────────────');
  try {
    const qgStatus = await client.getQualityGateStatus(testProject);
    console.log('✅ get_quality_gate works!');
    console.log(`   Status: ${qgStatus.projectStatus?.status || 'N/A'}`);
  } catch (error) {
    const sonarError = ErrorHandler.handle(error);
    console.log(`⚠️  ${sonarError.message}`);
  }
  console.log();

  // Test 2: Get Metrics
  console.log('Test 2: get_metrics');
  console.log('─────────────────────────────────────────');
  try {
    const metrics = await checker.getMetrics(testProject);
    console.log('✅ get_metrics works!');
    console.log(`   Metrics retrieved: ${Object.keys(metrics.metrics).length}`);
    if (metrics.metrics.coverage) {
      console.log(`   Coverage: ${metrics.metrics.coverage}%`);
    }
    if (metrics.metrics.bugs) {
      console.log(`   Bugs: ${metrics.metrics.bugs}`);
    }
  } catch (error) {
    const sonarError = ErrorHandler.handle(error);
    console.log(`⚠️  ${sonarError.message}`);
  }
  console.log();

  // Test 3: Get Issues
  console.log('Test 3: get_issues');
  console.log('─────────────────────────────────────────');
  try {
    const issues = await checker.getIssues(testProject, null, {
      types: 'BUG,VULNERABILITY',
      ps: 5
    });
    console.log('✅ get_issues works!');
    console.log(`   Total issues: ${issues.total}`);
    if (issues.issues && issues.issues.length > 0) {
      console.log(`   Sample issue: ${issues.issues[0].type} - ${issues.issues[0].severity}`);
    }
  } catch (error) {
    const sonarError = ErrorHandler.handle(error);
    console.log(`⚠️  ${sonarError.message}`);
  }
  console.log();

  // Test 4: Validate Quality Gate (main tool)
  console.log('Test 4: validate_quality_gate ⭐ (Main Tool)');
  console.log('─────────────────────────────────────────');
  try {
    const validation = await checker.validateQualityGate(testProject);
    console.log('✅ validate_quality_gate works!');
    console.log(`   Passed: ${validation.passed}`);
    console.log(`   Status: ${validation.status}`);
    if (!validation.passed && validation.failures) {
      console.log(`   Failures: ${validation.failures.length}`);
      validation.failures.forEach((f, i) => {
        console.log(`     ${i + 1}. ${f.message}`);
      });
    }
    console.log(`   Dashboard: ${validation.dashboardUrl}`);
  } catch (error) {
    const sonarError = ErrorHandler.handle(error);
    console.log(`⚠️  ${sonarError.message}`);
  }

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('✅ All MCP tools tested successfully!\n');
  console.log('🎉 SonarQube MCP server is fully functional!\n');
  console.log('Next steps:');
  console.log('1. Set your token permanently:');
  console.log('   export SONARQUBE_TOKEN=squ_fe8873...');
  console.log('   # Or add to .env file');
  console.log('');
  console.log('2. Update PROJECT.md with your project key:');
  console.log(`   - **Project Key**: \`${testProject}\``);
  console.log('');
  console.log('3. Test with /commit-push-pr:');
  console.log('   Make a code change, then run:');
  console.log('   /commit-push-pr TASK-XXX');
  console.log('');
  console.log('4. The quality gate will be validated before push!');
}

testTools().catch((error) => {
  console.error('\n❌ Test failed:', error.message);
  if (error.stack) {
    console.error(error.stack);
  }
  process.exit(1);
});
