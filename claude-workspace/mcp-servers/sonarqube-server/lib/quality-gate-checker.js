/**
 * Quality Gate Checker
 * Validates quality gate status and provides detailed failure information
 */

export class QualityGateChecker {
  constructor(client, baseUrl) {
    this.client = client;
    this.baseUrl = baseUrl;
  }

  /**
   * Validate if project passes quality gate
   * @param {string} projectKey - SonarQube project key
   * @param {string} branch - Branch name (optional)
   * @returns {Promise<Object>} Validation result with pass/fail and details
   */
  async validateQualityGate(projectKey, branch = null) {
    try {
      const status = await this.client.getQualityGateStatus(projectKey, branch);

      // Extract quality gate status
      const projectStatus = status.projectStatus;
      const gateStatus = projectStatus.status; // OK, WARN, or ERROR

      // Build dashboard URL
      const dashboardUrl = this.buildDashboardUrl(projectKey, branch);

      // If quality gate passed
      if (gateStatus === 'OK') {
        return {
          passed: true,
          status: 'OK',
          message: 'All quality gate conditions met',
          dashboardUrl
        };
      }

      // If quality gate failed or warned
      const failures = this.parseFailedConditions(projectStatus.conditions || []);

      return {
        passed: false,
        status: gateStatus,
        message: `Quality gate ${gateStatus.toLowerCase()}: ${failures.length} condition(s) failed`,
        failures,
        dashboardUrl
      };

    } catch (error) {
      // Re-throw error to be handled by error handler
      throw error;
    }
  }

  /**
   * Parse failed conditions from quality gate status
   * @param {Array} conditions - Quality gate conditions
   * @returns {Array<Object>} Parsed failed conditions
   */
  parseFailedConditions(conditions) {
    return conditions
      .filter(c => c.status === 'ERROR')
      .map(c => ({
        metric: c.metricKey,
        threshold: c.errorThreshold,
        actual: c.actualValue,
        comparator: c.comparator,
        message: this.formatConditionMessage(c)
      }));
  }

  /**
   * Format condition failure message
   * @param {Object} condition - Condition object from SonarQube
   * @returns {string} Human-readable message
   */
  formatConditionMessage(condition) {
    const metricNames = {
      'new_bugs': 'New Bugs',
      'new_vulnerabilities': 'New Vulnerabilities',
      'new_code_smells': 'New Code Smells',
      'new_coverage': 'Coverage on New Code',
      'new_duplicated_lines_density': 'Duplicated Lines on New Code',
      'new_security_hotspots': 'New Security Hotspots',
      'new_security_hotspots_reviewed': 'Security Hotspots Reviewed',
      'new_maintainability_rating': 'Maintainability Rating on New Code',
      'new_reliability_rating': 'Reliability Rating on New Code',
      'new_security_rating': 'Security Rating on New Code',
      'coverage': 'Overall Coverage',
      'bugs': 'Bugs',
      'vulnerabilities': 'Vulnerabilities',
      'code_smells': 'Code Smells',
      'security_hotspots_reviewed': 'Security Hotspots Reviewed (%)',
    };

    const metricName = metricNames[condition.metricKey] || condition.metricKey;
    const threshold = condition.errorThreshold;
    const actual = condition.actualValue;
    const comparator = condition.comparator;

    // Format based on comparator
    switch (comparator) {
      case 'GT': // Greater than (e.g., bugs > 0)
        return `${metricName}: ${actual} (threshold: ≤ ${threshold})`;
      case 'LT': // Less than (e.g., coverage < 80%)
        return `${metricName}: ${actual}% (threshold: ≥ ${threshold}%)`;
      default:
        return `${metricName}: ${actual} (threshold: ${threshold})`;
    }
  }

  /**
   * Build SonarQube dashboard URL for a project/branch
   * @param {string} projectKey - Project key
   * @param {string} branch - Branch name (optional)
   * @returns {string} Dashboard URL
   */
  buildDashboardUrl(projectKey, branch) {
    let url = `${this.baseUrl}/dashboard?id=${encodeURIComponent(projectKey)}`;
    if (branch) {
      url += `&branch=${encodeURIComponent(branch)}`;
    }
    return url;
  }

  /**
   * Get detailed issues for a project
   * @param {string} projectKey - Project key
   * @param {string} branch - Branch name (optional)
   * @param {Object} filters - Issue filters
   * @returns {Promise<Object>} Issues with categorization
   */
  async getIssues(projectKey, branch = null, filters = {}) {
    const options = {
      branch,
      ...filters,
      resolved: false // Only unresolved issues
    };

    const result = await this.client.searchIssues(projectKey, options);

    return {
      total: result.total || 0,
      issues: result.issues || [],
      dashboardUrl: this.buildDashboardUrl(projectKey, branch)
    };
  }

  /**
   * Get code metrics for a project
   * @param {string} projectKey - Project key
   * @param {string} branch - Branch name (optional)
   * @param {Array<string>} metricKeys - Specific metrics to retrieve
   * @returns {Promise<Object>} Metrics with formatted values
   */
  async getMetrics(projectKey, branch = null, metricKeys = []) {
    const result = await this.client.getMetrics(projectKey, branch, metricKeys);

    const measures = result.component?.measures || [];
    const metricsObj = {};

    measures.forEach(measure => {
      metricsObj[measure.metric] = measure.value;
    });

    return {
      projectKey,
      branch,
      metrics: metricsObj,
      dashboardUrl: this.buildDashboardUrl(projectKey, branch)
    };
  }
}
