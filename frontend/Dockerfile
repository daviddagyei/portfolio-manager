# Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Set environment variable for port
ENV PORT=3030

# Expose port
EXPOSE 3030

# Command to run the application
CMD ["npm", "start"]
