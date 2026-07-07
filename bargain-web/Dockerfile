FROM node:24-slim

# CACHE BUST: 2026-07-04 - Force Railway snapshot cache invalidation

WORKDIR /app

# Pin pnpm to v9 to avoid pnpm v11 "approve-builds" prompts in CI.
RUN corepack enable && corepack prepare pnpm@9.15.5 --activate

# Copy package manifest (lockfile lives at monorepo root, not in bargain-web/)
COPY package.json ./

# Install dependencies (frozen-lockfile=false because lockfile is at repo root)
RUN pnpm install --frozen-lockfile=false

# Copy source code
COPY . .

# Force rebuild timestamp: 2025-07-04T00:00:00Z
RUN echo "Force rebuild for Next.js deployment"

# Remove any stale .next folder to ensure fresh build
RUN rm -rf .next

# Always compile fresh
RUN pnpm run build

ENV NODE_ENV=production
ENV PORT=3030
EXPOSE 3030

CMD ["sh", "-c", "node .next/standalone/bargain-web/server.js"]
