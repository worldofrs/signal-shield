# --- FRONTEND DOCKERFILE ---
# This one is more complex because it uses "multi-stage builds."
# The idea: use one big image to BUILD the app, then copy only the
# output into a tiny image to RUN it. This keeps the final image small.

# ============================================
# STAGE 1: "builder" — install deps and build
# ============================================
# We name this stage "builder" so we can reference it later.
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first (same caching trick as the backend)
#
# YOUR TURN: Uncomment the lines below
# COPY package.json package-lock.json ./
# RUN npm ci

# Copy source code and build the production bundle
# "npm run build" compiles TypeScript, optimizes CSS, bundles everything
# into a .next folder. With output: "standalone", it also creates a
# self-contained server in .next/standalone.
#
# YOUR TURN: Uncomment the lines below
# COPY . .
# RUN npm run build

# ============================================
# STAGE 2: "runner" — the actual production image
# ============================================
# Start fresh from a clean alpine image. Nothing from stage 1 carries
# over unless we explicitly COPY it. This means node_modules, source
# files, and build tools are all thrown away.
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy only what we need from the builder stage:
# 1. The standalone server (includes only the Node.js code needed to run)
# 2. Static assets (CSS, JS bundles the browser downloads)
# 3. Public folder (favicon, images)
#
# Next.js standalone doesn't include static/ and public/ automatically,
# so we must copy them explicitly — this is a common gotcha.
#
# YOUR TURN: Uncomment the lines below
# COPY --from=builder /app/.next/standalone ./
# COPY --from=builder /app/.next/static ./.next/static
# COPY --from=builder /app/public ./public

# Start the server. Next.js standalone outputs a server.js file
# that's a self-contained Node.js server.
#
# YOUR TURN: Uncomment the line below
# CMD ["sh", "-c", "PORT=${PORT:-3000} node server.js"]
