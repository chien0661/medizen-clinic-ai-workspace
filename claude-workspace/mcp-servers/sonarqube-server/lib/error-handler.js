/**
 * Error Handler for SonarQube MCP Server
 * Categorizes and formats errors with actionable guidance
 */

export class SonarQubeError extends Error {
  constructor(message, code, statusCode = null, details = null) {
    super(message);
    this.name = 'SonarQubeError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

export class ErrorHandler {
  /**
   * Handle and categorize errors from SonarQube API
   * @param {Error} error - The error to handle
   * @returns {SonarQubeError} Categorized error with guidance
   */
  static handle(error) {
    // Network/Connection errors
    if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND' || error.code === 'ETIMEDOUT') {
      return new SonarQubeError(
        'Cannot reach SonarQube server. Please verify the server is accessible.',
        'SONARQUBE_UNREACHABLE',
        null,
        {
          cause: error.message,
          action: 'BLOCK',
          guidance: [
            'Verify SonarQube server is running: https://sonarqube.vissoft.vn',
            'Check network connectivity',
            'Verify firewall settings allow access',
          ]
        }
      );
    }

    // HTTP status code errors
    if (error.statusCode) {
      switch (error.statusCode) {
        case 401:
          return new SonarQubeError(
            'Authentication failed. Invalid or missing SonarQube token.',
            'AUTHENTICATION_FAILED',
            401,
            {
              cause: 'Invalid SONARQUBE_TOKEN',
              action: 'BLOCK',
              guidance: [
                'Verify SONARQUBE_TOKEN environment variable is set',
                'Check token is valid (not expired)',
                'Generate new token: My Account → Security → Generate Token',
                'Set environment: export SONARQUBE_TOKEN=squ_xxxx',
              ]
            }
          );

        case 403:
          return new SonarQubeError(
            'Access forbidden. Token lacks required permissions.',
            'INSUFFICIENT_PERMISSIONS',
            403,
            {
              cause: 'Token missing permissions',
              action: 'BLOCK',
              guidance: [
                'Verify token has "Browse" permission on project',
                'Check token has "Execute Analysis" permission if needed',
                'Contact SonarQube administrator for access',
              ]
            }
          );

        case 404:
          return new SonarQubeError(
            'Project not found in SonarQube.',
            'PROJECT_NOT_FOUND',
            404,
            {
              cause: 'Invalid project key or project not analyzed',
              action: 'BLOCK',
              guidance: [
                'Verify project key in PROJECT.md is correct',
                'Check project exists in SonarQube',
                'Run initial analysis if project is new: mvn sonar:sonar',
                'Visit: https://sonarqube.vissoft.vn/projects',
              ]
            }
          );

        case 500:
        case 502:
        case 503:
        case 504:
          return new SonarQubeError(
            'SonarQube server error. Please try again later.',
            'SERVER_ERROR',
            error.statusCode,
            {
              cause: `HTTP ${error.statusCode}`,
              action: 'BLOCK',
              guidance: [
                'SonarQube server is experiencing issues',
                'Wait a few minutes and try again',
                'Check SonarQube server status',
                'Contact SonarQube administrator if persists',
              ]
            }
          );

        default:
          return new SonarQubeError(
            `SonarQube API error: HTTP ${error.statusCode}`,
            'API_ERROR',
            error.statusCode,
            {
              cause: error.message,
              action: 'BLOCK',
              guidance: [
                'Unexpected API error occurred',
                'Check SonarQube API documentation',
                'Contact support with error details',
              ]
            }
          );
      }
    }

    // JSON parsing errors
    if (error instanceof SyntaxError) {
      return new SonarQubeError(
        'Invalid response from SonarQube. Response is not valid JSON.',
        'INVALID_RESPONSE',
        null,
        {
          cause: 'Malformed JSON response',
          action: 'BLOCK',
          guidance: [
            'SonarQube returned invalid data',
            'This may indicate server issues',
            'Try again or contact SonarQube administrator',
          ]
        }
      );
    }

    // Generic/unknown errors
    return new SonarQubeError(
      error.message || 'Unknown error occurred',
      'UNKNOWN_ERROR',
      null,
      {
        cause: error.stack || 'No stack trace available',
        action: 'BLOCK',
        guidance: [
          'An unexpected error occurred',
          'Check server logs for details',
          'Report issue if problem persists',
        ]
      }
    );
  }

  /**
   * Format error for MCP response
   * @param {SonarQubeError} error - The error to format
   * @returns {Object} MCP error response
   */
  static formatErrorResponse(error) {
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          passed: false,
          status: 'ERROR',
          error: error.code,
          message: error.message,
          details: error.details,
        }, null, 2)
      }],
      isError: true
    };
  }
}
