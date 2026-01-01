# 第一阶段：构建
FROM node:20-slim AS builder

# 设置 pnpm
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app

# 复制 package.json 和 lock 文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 设置构建时的内存限制，防止 OOM (Exit code 137)
ENV NODE_OPTIONS="--max-old-space-size=2048"

# 复制源文件
COPY . .

# 执行构建（SSR 模式需要构建后运行服务器）
# 确保在构建前环境变量已经正确设置，或者在构建时通过 ARG 传入
ARG PUBLIC_API_URL=http://firefly-backend:8000
ENV PUBLIC_API_URL=$PUBLIC_API_URL

RUN pnpm build

# 第二阶段：运行时
FROM node:20-slim AS runner

WORKDIR /app

# 复制构建产物
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# 设置运行时环境变量
ENV HOST=0.0.0.0
ENV PORT=4321
ENV NODE_ENV=production

# 暴露端口
EXPOSE 4321

# 使用 node 运行构建出的 entrypoint
CMD ["node", "./dist/server/entry.mjs"]
