FROM node:24-slim

# CACHE BUST: 2025-06-30 - Force Railway snapshot cache invalidation

WORKDIR /app

# Pin pnpm to v9 to avoid pnpm v11 "approve-builds" prompts in CI.
RUN corepack enable && corepack prepare pnpm@9.15.1 --activate

# Copy workspace manifests first (better caching)
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY bargain-web/package.json ./bargain-web/package.json

# Install workspace dependencies
RUN pnpm install --frozen-lockfile --ignore-scripts=false

# Copy source code
COPY bargain-web ./bargain-web

# Force rebuild timestamp: 2025-06-30T00:00:00Z
RUN echo "Force rebuild for Next.js deployment"

# Remove any stale .next folder to ensure fresh build
RUN rm -rf bargain-web/.next

# Always compile fresh
RUN pnpm -C bargain-web run build

ENV NODE_ENV=production
EXPOSE 3000

CMD ["node", "bargain-web/.next/standalone/server.js"]
