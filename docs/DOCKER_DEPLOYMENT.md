# Firefly CMS Docker 部署指南

本指南将帮助你使用 Docker 和 Docker Compose 快速部署 Firefly CMS。

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 10GB 可用磁盘空间

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/deer-king/Firefly-CMS.git
cd Firefly-CMS
```

### 2. 配置环境变量

复制环境变量示例文件并根据需要修改：

```bash
cp .env.example .env
```

重要配置项说明：

```env
# 数据库配置
MYSQL_ROOT_PASSWORD=your_secure_root_password    # MySQL root 密码
MYSQL_DATABASE=firefly_cms                        # 数据库名
MYSQL_USER=firefly                                # 数据库用户
MYSQL_PASSWORD=your_secure_password               # 数据库密码

# JWT 配置
JWT_SECRET_KEY=your_very_secure_random_key        # JWT 密钥（必须修改）
JWT_ALGORITHM=HS256                               # JWT 算法

# 后端配置
BACKEND_CORS_ORIGINS=http://localhost:4321,http://localhost  # 允许的前端域名
UPLOAD_DIR=/app/uploads                           # 上传目录
MAX_UPLOAD_SIZE=10485760                          # 最大上传大小（10MB）
```

**⚠️ 安全提示：** 在生产环境中，请务必修改所有默认密码和密钥！

### 3. 启动服务

#### 标准部署（MySQL + Backend + Frontend）

```bash
docker-compose up -d
```

#### 包含 Nginx 反向代理的完整部署

```bash
docker-compose --profile with-nginx up -d
```

### 4. 查看服务状态

```bash
docker-compose ps
```

预期输出：

```
NAME                SERVICE     STATUS      PORTS
firefly-backend     backend     running     0.0.0.0:8000->8000/tcp
firefly-frontend    frontend    running     0.0.0.0:4321->4321/tcp
firefly-mysql       mysql       running     0.0.0.0:3306->3306/tcp
firefly-nginx       nginx       running     0.0.0.0:80->80/tcp (仅在使用 with-nginx 时)
```

### 5. 访问应用

- **前端页面**: http://localhost:4321
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **完整站点** (使用 Nginx): http://localhost

### 6. 默认管理员账号

- **用户名**: `admin`
- **密码**: `admin123`

**⚠️ 首次登录后请立即修改密码！**

## 🔧 常用命令

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 停止服务

```bash
# 停止所有服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器、网络、数据卷（⚠️ 会删除所有数据）
docker-compose down -v
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# 进入数据库容器
docker-compose exec mysql mysql -u root -p
```

## 📦 数据持久化

Docker Compose 会自动创建以下数据卷：

- `mysql_data`: MySQL 数据库文件
- `backend_uploads`: 后端上传的文件
- `nginx_logs`: Nginx 日志（使用 with-nginx 时）

### 备份数据

```bash
# 备份数据库
docker-compose exec mysql mysqldump -u root -p firefly_cms > backup_$(date +%Y%m%d).sql

# 备份上传文件
docker run --rm -v firefly-cms_backend_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads_$(date +%Y%m%d).tar.gz -C /data .
```

### 恢复数据

```bash
# 恢复数据库
docker-compose exec -T mysql mysql -u root -p firefly_cms < backup.sql

# 恢复上传文件
docker run --rm -v firefly-cms_backend_uploads:/data -v $(pwd):/backup alpine tar xzf /backup/uploads.tar.gz -C /data
```

## 🔐 生产环境配置

### 1. 使用强密码

生成安全的随机密钥：

```bash
# 生成 JWT 密钥
openssl rand -hex 32

# 生成数据库密码
openssl rand -base64 32
```

### 2. 配置 HTTPS

修改 [`nginx/conf.d/default.conf`](nginx/conf.d/default.conf)，添加 SSL 配置：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 其他配置...
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

在 [`docker-compose.yml`](docker-compose.yml) 中挂载 SSL 证书：

```yaml
nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/conf.d:/etc/nginx/conf.d:ro
    - ./ssl:/etc/nginx/ssl:ro  # 添加这行
```

### 3. 限制端口暴露

在生产环境中，只暴露 Nginx 端口（80/443），不直接暴露其他服务端口。

修改 [`docker-compose.yml`](docker-compose.yml)：

```yaml
backend:
  # ports:
  #   - "8000:8000"  # 注释掉，只通过 Nginx 访问
  expose:
    - "8000"

frontend:
  # ports:
  #   - "4321:4321"  # 注释掉，只通过 Nginx 访问
  expose:
    - "4321"

mysql:
  # ports:
  #   - "3306:3306"  # 注释掉，只允许内部访问
  expose:
    - "3306"
```

### 4. 启用防火墙

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 5. 配置自动备份

创建备份脚本 `backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
docker-compose exec -T mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD firefly_cms > "$BACKUP_DIR/db_$DATE.sql"

# 备份上传文件
docker run --rm -v firefly-cms_backend_uploads:/data -v "$BACKUP_DIR":/backup alpine tar czf "/backup/uploads_$DATE.tar.gz" -C /data .

# 保留最近 7 天的备份
find "$BACKUP_DIR" -name "db_*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +7 -delete
```

添加到 crontab（每天凌晨 2 点执行）：

```bash
crontab -e
# 添加：
0 2 * * * /path/to/backup.sh
```

## 🐛 故障排查

### 数据库连接失败

1. 检查 MySQL 容器是否正常运行：
   ```bash
   docker-compose ps mysql
   docker-compose logs mysql
   ```

2. 验证环境变量配置是否正确

3. 等待 MySQL 完全启动（首次启动需要初始化，可能需要 1-2 分钟）

### 前端无法访问后端 API

1. 检查 CORS 配置：
   ```bash
   # 查看后端环境变量
   docker-compose exec backend env | grep CORS
   ```

2. 确保 [`BACKEND_CORS_ORIGINS`](.env:11) 包含前端地址

3. 检查网络连接：
   ```bash
   docker-compose exec frontend ping backend
   ```

### 容器无法启动

1. 查看详细错误日志：
   ```bash
   docker-compose logs --tail=100
   ```

2. 检查端口占用：
   ```bash
   # Linux/Mac
   sudo netstat -tlnp | grep -E ':(80|443|3306|4321|8000)'
   
   # Windows
   netstat -ano | findstr "80 443 3306 4321 8000"
   ```

3. 清理并重新构建：
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### 磁盘空间不足

清理未使用的 Docker 资源：

```bash
# 清理停止的容器
docker container prune -f

# 清理未使用的镜像
docker image prune -a -f

# 清理未使用的数据卷（⚠️ 小心操作）
docker volume prune -f

# 一键清理所有未使用的资源
docker system prune -a --volumes -f
```

## 📊 性能优化

### 1. 数据库优化

在 [`docker-compose.yml`](docker-compose.yml) 中添加 MySQL 配置：

```yaml
mysql:
  command: 
    - --character-set-server=utf8mb4
    - --collation-server=utf8mb4_unicode_ci
    - --max_connections=200
    - --innodb_buffer_pool_size=512M
    - --query_cache_size=32M
```

### 2. 前端构建优化

在 [`Dockerfile`](Dockerfile) 中调整构建参数：

```dockerfile
# 启用生产优化
ENV NODE_ENV=production
ENV ASTRO_TELEMETRY_DISABLED=1

# 增加 Node.js 内存限制（如果需要）
ENV NODE_OPTIONS="--max-old-space-size=4096"
```

### 3. Nginx 缓存配置

在 [`nginx/conf.d/default.conf`](nginx/conf.d/default.conf) 中添加缓存：

```nginx
# 静态资源缓存
location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🔄 更新与升级

### 更新应用代码

```bash
# 1. 拉取最新代码
git pull origin master

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d
```

### 数据库迁移

如果有数据库结构变更，需要执行迁移脚本：

```bash
# 进入后端容器
docker-compose exec backend bash

# 执行迁移（具体命令取决于你的迁移工具）
# 例如使用 Alembic:
# alembic upgrade head
```

## 📚 其他资源

- [Firefly CMS GitHub](https://github.com/deer-king/Firefly-CMS)
- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Astro 文档](https://docs.astro.build/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

## 💬 获取帮助

如果遇到问题：

1. 查看本文档的故障排查部分
2. 在 [GitHub Issues](https://github.com/deer-king/Firefly-CMS/issues) 搜索类似问题
3. 提交新的 Issue 并提供详细的错误日志

---

**祝你使用愉快！** 🎉