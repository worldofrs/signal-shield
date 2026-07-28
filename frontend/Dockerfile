# --- FRONTEND DOCKERFILE ---
# Uses "multi-stage builds" — build in a big image, then copy only the
# output into a tiny image to run. Keeps the final image small.

# ============================================
# STAGE 1: "builder" — install deps and build
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first (same caching trick as the backend)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code and build the production bundle.
# NEXT_PUBLIC_ env vars must be set at BUILD time because Next.js
# inlines them into the JavaScript bundle during compilation.
COPY . .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# ============================================
# STAGE 2: "runner" — the actual production image
# ============================================
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy only what we need from the builder stage:
# 1. The standalone server (self-contained Node.js server)
# 2. Static assets (CSS, JS bundles the browser downloads)
# 3. Public folder (favicon, images)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Start the server. Next.js standalone outputs a server.js file.
CMD ["sh", "-c", "PORT=${PORT:-3000} node server.js"]
