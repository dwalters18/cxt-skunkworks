# Build the React app, then serve it with nginx.
#
# The Google Maps key is baked at build time (CRA). Priority:
#   1. GOOGLE_MAPS_API_KEY build arg (passed through by docker-compose from the host env)
#   2. ui/.env if present on the build machine (git-ignored)
#   3. none — the app still runs; the dispatch map shows a fallback panel
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG GOOGLE_MAPS_API_KEY=""
RUN if [ -n "$GOOGLE_MAPS_API_KEY" ]; then \
      echo "REACT_APP_GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY" > .env.production.local; \
    fi \
    && npm run build

FROM nginx:stable-alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
