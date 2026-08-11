# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY frontend/ .

# Build for production
RUN npm run build

# Production stage
FROM node:20-alpine AS production

WORKDIR /app

# Install serve for static file serving
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Create non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001

USER appuser

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["serve", "-s", "dist", "-l", "3000"]
