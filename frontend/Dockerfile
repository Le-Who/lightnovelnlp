# Stage 1: Builder
FROM node:20-alpine AS builder

# Enable pnpm via corepack
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy dependency definitions first to leverage Docker cache
COPY package.json pnpm-lock.yaml ./

# Install dependencies (frozen-lockfile ensures reproducibility)
RUN pnpm install --frozen-lockfile

# Copy the rest of the source code
COPY . .

# Build argument for API URL (required for Vite at build time)
ARG VITE_API_URL=https://p01--lightnovelnlp--95w5j7vcjd9s.code.run
ENV VITE_API_URL=$VITE_API_URL

# Debug: List files to verify copy
RUN ls -R /app/src

# Build the application
RUN pnpm run build

# Stage 2: Production
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config (ensure this file exists in your frontend directory)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 8080 (standard for cloud runners)
EXPOSE 8080

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
