# 零依赖运行时 Dockerfile (推荐用于 standalone 模式)
# 只要你在本地使用了 node adapter 的 standalone 模式构建，dist 就是自包含的
FROM node:20-slim

WORKDIR /app

# 只需要复制构建产物 dist
# COPY dist ./dist

# 设置运行时环境变量
ENV HOST=0.0.0.0
ENV PORT=4321
ENV NODE_ENV=production

# 暴露端口
EXPOSE 4321

# 运行自包含的 entry point
CMD ["node", "./dist/server/entry.mjs"]
