FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install git and pnpm
RUN apk add --no-cache git && npm install -g pnpm

# Clone the repo into container
RUN git clone https://github.com/langchain-ai/agent-chat-ui.git . \
    && pnpm install \
    && pnpm build

EXPOSE 3000

CMD ["pnpm", "dev"]
