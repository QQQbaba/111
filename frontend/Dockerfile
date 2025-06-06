# Build stage
FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage - just copy files
FROM alpine:latest

# Install basic tools
RUN apk add --no-cache rsync

# Copy built files
COPY --from=build /app/dist /dist

# Copy files to volume and keep container alive
CMD ["sh", "-c", "rsync -av /dist/ /usr/share/nginx/html/ && echo 'Frontend build copied successfully' && tail -f /dev/null"]
