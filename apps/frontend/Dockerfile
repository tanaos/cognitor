# ── Stage 1: build ──────────────────────────────────────────────────────────
FROM node:22-alpine AS builder
WORKDIR /app

# Allow overriding the API URL at build time (server components resolve this at request time via env, but bake it in for safety)
ARG NEXT_PUBLIC_API_URL=http://backend:3001
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Copy monorepo manifests and install all deps
COPY package.json package-lock.json ./
COPY apps/frontend/package.json ./apps/frontend/
COPY packages/shared/package.json ./packages/shared/

RUN npm ci --workspace=packages/shared --workspace=apps/frontend

# Copy source
COPY packages/shared ./packages/shared
COPY apps/frontend ./apps/frontend

# Build shared types first, then Next.js
RUN npm run build --workspace=packages/shared
RUN npm run build --workspace=apps/frontend

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY package.json package-lock.json ./
COPY apps/frontend/package.json ./apps/frontend/
COPY packages/shared/package.json ./packages/shared/

RUN npm ci --workspace=packages/shared --workspace=apps/frontend --omit=dev

COPY --from=builder /app/apps/frontend/.next ./apps/frontend/.next
COPY --from=builder /app/apps/frontend/public ./apps/frontend/public
COPY --from=builder /app/packages/shared/dist ./packages/shared/dist

EXPOSE 3000

CMD ["npm", "run", "start", "--workspace=apps/frontend"]
