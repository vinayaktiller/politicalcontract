# frontend/Dockerfile
FROM node:18

WORKDIR /app
COPY package*.json ./
RUN npm install

# Add these for Windows compatibility
ENV WATCHPACK_POLLING=true
ENV CHOKIDAR_USEPOLLING=true

CMD ["npm", "start"]