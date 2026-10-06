FROM node:22-bookworm AS build
WORKDIR /app
ARG NPM_TOKEN
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc
COPY package.json ./
RUN npm install --omit=dev
COPY src ./src

FROM node:22-bookworm-slim
WORKDIR /app
COPY --from=build /app /app
USER node
EXPOSE 8080
CMD ["node", "src/server.js"]
