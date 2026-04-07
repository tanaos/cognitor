# ── Stage 1: build ──────────────────────────────────────────────────────────
FROM node:22-alpine AS builder
WORKDIR /app

# Copy monorepo manifests and install all deps
COPY package.json package-lock.json ./
COPY apps/backend/package.json ./apps/backend/
COPY packages/shared/package.json ./packages/shared/

RUN npm ci --workspace=packages/shared --workspace=apps/backend

# Copy source
COPY packages/shared ./packages/shared
COPY apps/backend ./apps/backend

# Build shared first, then backend
RUN npm run build --workspace=packages/shared
RUN npm run build --workspace=apps/backend

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY package.json package-lock.json ./
COPY apps/backend/package.json ./apps/backend/
COPY packages/shared/package.json ./packages/shared/

RUN npm ci --workspace=packages/shared --workspace=apps/backend --omit=dev

COPY --from=builder /app/packages/shared/dist ./packages/shared/dist
COPY --from=builder /app/apps/backend/dist ./apps/backend/dist

EXPOSE 3001

CMD ["node", "apps/backend/dist/main.js"]
