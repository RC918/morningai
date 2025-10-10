FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN corepack enable && npm i --omit=dev
COPY server.js ./
ENV PORT=3000 NODE_ENV=production
EXPOSE 3000
CMD ["npm","start"]
