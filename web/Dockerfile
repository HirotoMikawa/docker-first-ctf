FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Set environment variable for Next.js
ENV NODE_ENV=development

# Run development server
# -H 0.0.0.0 で全インターフェースにバインド（コンテナ外からアクセス可能に）
CMD ["npm", "run", "dev"]



