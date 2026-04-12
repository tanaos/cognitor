FROM node:22-alpine AS builder
WORKDIR /app

# Install workspace dependencies first for better layer caching.
COPY package.json package-lock.json ./
COPY apps/backend/package.json ./apps/backend/
COPY apps/frontend/package.json ./apps/frontend/
COPY packages/shared/package.json ./packages/shared/

RUN npm ci

COPY . .

RUN npm run build --workspace=packages/shared
RUN npm run build --workspace=apps/backend
RUN npm run build --workspace=apps/frontend
RUN npm prune --omit=dev

FROM node:22-alpine AS runner
WORKDIR /app

RUN apk add --no-cache postgresql18 postgresql18-client su-exec

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV BACKEND_INTERNAL_URL=http://127.0.0.1:3001
ENV NEXT_PUBLIC_API_URL=/api
ENV DB_HOST=127.0.0.1
ENV DB_PORT=5432
ENV DB_USER=cognitoruser
ENV DB_PASSWORD=cognitorpassword
ENV DB_NAME=cognitor
ENV PGDATA=/var/lib/postgresql/data/pg18

COPY package.json package-lock.json ./
COPY apps/backend/package.json ./apps/backend/
COPY apps/frontend/package.json ./apps/frontend/
COPY packages/shared/package.json ./packages/shared/

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/apps/backend ./apps/backend
COPY --from=builder /app/apps/frontend ./apps/frontend
COPY --from=builder /app/packages/shared ./packages/shared

COPY scripts/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 3000
EXPOSE 3001
EXPOSE 5432

CMD ["/usr/local/bin/entrypoint.sh"]