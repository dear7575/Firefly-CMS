#!/bin/bash

# Firefly CMS Docker 快速启动脚本
# 适用于 Linux/Mac 系统

set -e

echo "======================================"
echo "   Firefly CMS Docker 快速启动"
echo "======================================"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未找到 Docker，请先安装 Docker"
    echo "   访问: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ 错误: 未找到 Docker Compose，请先安装 Docker Compose"
    echo "   访问: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "🐳 正在启动 Docker 容器..."
echo ""
echo "🚀 启动服务（MySQL + Backend + Frontend）..."
docker-compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态："
docker-compose ps

echo ""
echo "======================================"
echo "   ✅ Firefly CMS 启动完成！"
echo "======================================"
echo ""
echo "访问地址："
echo "  🌐 网站首页: http://localhost"
echo "  📊 后台管理: http://localhost/admin"
echo "  📚 API 文档: http://localhost/api/docs"
echo ""
echo "默认管理员账号："
echo "  👤 用户名: admin"
echo "  🔑 密码: admin123"
echo "  ⚠️  请登录后立即修改密码！"
echo ""
echo "常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose stop"
echo "  重启服务: docker-compose restart"
echo "  删除容器: docker-compose down"
echo ""
echo "📖 详细文档: ./docs/DOCKER_DEPLOYMENT.md"
echo ""