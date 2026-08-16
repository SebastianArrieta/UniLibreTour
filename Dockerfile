# Imagen del servidor Node.js + TypeScript
# Etapas: instalar dependencias → compilar → ejecutar

# Etapa 1: dependencias
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
# COPY backend/package*.json ./backend/
# RUN npm ci

# Etapa 2: build
FROM node:20-alpine AS build
WORKDIR /app
# COPY --from=deps /app/node_modules ./node_modules
# COPY . .
# RUN npm run build

# Etapa 3: producción
FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
# COPY --from=build /app/backend/dist ./backend/dist
# COPY --from=build /app/frontend/dist ./frontend/dist
EXPOSE 3000
# CMD ["node", "backend/dist/index.js"]
