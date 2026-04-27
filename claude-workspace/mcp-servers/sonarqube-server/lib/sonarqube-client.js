/**
 * SonarQube API Client
 * Handles HTTP requests to SonarQube REST API
 */

import https from 'https';
import http from 'http';
import { URL } from 'url';

export class SonarQubeClient {
  constructor(config) {
    this.baseUrl = config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.token = config.token;
    this.timeout = config.timeout || 30000; // 30 second default timeout
  }

  /**
   * Get authorization header for API requests
   * SonarQube uses Basic Auth with token as username, empty password
   */
  getAuthHeader() {
    const auth = Buffer.from(`${this.token}:`).toString('base64');
    return `Basic ${auth}`;
  }

  /**
   * Make HTTP request to SonarQube API
   * @param {string} endpoint - API endpoint path
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Parsed JSON response
   */
  async request(endpoint, params = {}) {
    return new Promise((resolve, reject) => {
      try {
        const url = new URL(`${this.baseUrl}${endpoint}`);

        // Add query parameters
        Object.keys(params).forEach(key => {
          if (params[key] !== undefined && params[key] !== null) {
            url.searchParams.append(key, params[key]);
          }
        });

        const isHttps = url.protocol === 'https:';
        const httpModule = isHttps ? https : http;

        const options = {
          method: 'GET',
          headers: {
            'Authorization': this.getAuthHeader(),
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          timeout: this.timeout,
        };

        const req = httpModule.request(url, options, (res) => {
          let data = '';

          res.on('data', chunk => {
            data += chunk;
          });

          res.on('end', () => {
            // Check for error status codes
            if (res.statusCode >= 400) {
              const error = new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`);
              error.statusCode = res.statusCode;
              error.response = data;
              return reject(error);
            }

            try {
              const parsed = JSON.parse(data);
              resolve(parsed);
            } catch (err) {
              err.response = data;
              reject(err);
            }
          });
        });

        req.on('error', (error) => {
          reject(error);
        });

        req.on('timeout', () => {
          req.destroy();
          const error = new Error('Request timeout');
          error.code = 'ETIMEDOUT';
          reject(error);
        });

        req.end();

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Get quality gate status for a project
   * API: GET /api/qualitygates/project_status
   * @param {string} projectKey - SonarQube project key
   * @param {string} branch - Branch name (optional)
   * @returns {Promise<Object>} Quality gate status
   */
  async getQualityGateStatus(projectKey, branch = null) {
    const params = { projectKey };
    if (branch) {
      params.branch = branch;
    }

    return await this.request('/api/qualitygates/project_status', params);
  }

  /**
   * Search for issues in a project
   * API: GET /api/issues/search
   * @param {string} projectKey - SonarQube project key
   * @param {Object} options - Filter options
   * @returns {Promise<Object>} Issues search results
   */
  async searchIssues(projectKey, options = {}) {
    const params = {
      projectKeys: projectKey,
      ...options
    };

    return await this.request('/api/issues/search', params);
  }

  /**
   * Get code metrics for a project
   * API: GET /api/measures/component
   * @param {string} projectKey - SonarQube project key
   * @param {string} branch - Branch name (optional)
   * @param {Array<string>} metricKeys - Metrics to retrieve
   * @returns {Promise<Object>} Metrics data
   */
  async getMetrics(projectKey, branch = null, metricKeys = []) {
    const defaultMetrics = [
      'coverage',
      'new_coverage',
      'bugs',
      'new_bugs',
      'vulnerabilities',
      'new_vulnerabilities',
      'code_smells',
      'new_code_smells',
      'security_hotspots',
      'new_security_hotspots',
      'security_hotspots_reviewed',
      'new_security_hotspots_reviewed'
    ];

    const metrics = metricKeys.length > 0 ? metricKeys : defaultMetrics;

    const params = {
      component: projectKey,
      metricKeys: metrics.join(',')
    };

    if (branch) {
      params.branch = branch;
    }

    return await this.request('/api/measures/component', params);
  }
}
