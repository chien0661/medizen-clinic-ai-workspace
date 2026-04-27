# Dockerfile for Claude Memory Worker
# Multi-stage build for optimized image size

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY mcp-servers/claude-mem-server/package*.json ./
COPY mcp-servers/claude-mem-server/tsconfig.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm install -D typescript tsx @types/node

# Copy source code
COPY mcp-servers/claude-mem-server/src ./src

# Build TypeScript
RUN npm run build

# Stage 2: Production
FROM node:20-alpine

# Create app user for security
RUN addgroup -g 1001 -S claudemem && \
    adduser -S claudemem -u 1001

WORKDIR /opt/claude-memory

# Copy built application
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules

# Create directories for data and logs
RUN mkdir -p /opt/claude-memory/data \
             /opt/claude-memory/logs \
             /opt/claude-memory/backups && \
    chown -R claudemem:claudemem /opt/claude-memory

# Switch to non-root user
USER claudemem

# Expose worker port
EXPOSE 37777

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:37777/api/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1); }).on('error', () => process.exit(1));"

# Start worker service
CMD ["node", "dist/services/worker.js"]
