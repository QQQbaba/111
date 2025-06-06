#!/bin/bash

# 网络自习室生产部署脚本

set -e

echo "🚀 开始部署网络自习室..."

# 检查是否为 root 用户
if [[ $EUID -eq 0 ]]; then
   echo "❌ 请不要使用 root 用户运行此脚本"
   exit 1
fi

# 检查系统要求
echo "🔍 检查系统要求..."

# 检查 Ubuntu 版本
if ! grep -q "Ubuntu 22.04" /etc/os-release; then
    echo "⚠️  推荐使用 Ubuntu 22.04 LTS"
fi

# 安装系统依赖
echo "📦 安装系统依赖..."
sudo apt update
sudo apt install -y \
    docker.io \
    docker-compose \
    lxcfs \
    curl \
    wget \
    git

# 启动并启用服务
echo "🔧 配置系统服务..."
sudo systemctl enable --now docker
sudo systemctl enable --now lxcfs

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

echo "👥 用户已添加到 docker 组，请重新登录或运行 'newgrp docker'"

# 检查 lxcfs 是否正常工作
if [ ! -d "/var/lib/lxcfs/proc" ]; then
    echo "❌ lxcfs 未正确配置"
    exit 1
fi

# 创建项目目录
PROJECT_DIR="/opt/studyroom"
echo "📁 创建项目目录: $PROJECT_DIR"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# 克隆或更新代码
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "🔄 更新代码..."
    cd $PROJECT_DIR
    git pull
else
    echo "📥 克隆代码..."
    git clone https://github.com/webwww123/111.git $PROJECT_DIR
    cd $PROJECT_DIR
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data/redis
chmod 755 data

# 生成生产环境配置
echo "⚙️  生成生产环境配置..."
cat > .env.production << EOF
# 生产环境配置
JWT_SECRET=$(openssl rand -hex 32)
REDIS_URL=redis://redis:6379
DB_PATH=/data/app.db
NODE_ENV=production
EOF

# 构建镜像
echo "🔨 构建生产镜像..."
docker-compose build

# 启动服务
echo "🎯 启动生产服务..."
docker-compose -f docker-compose.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "📋 检查服务状态..."
docker-compose ps

# 创建管理员账号
echo ""
echo "👤 创建管理员账号..."
read -p "请输入管理员用户名: " ADMIN_USER
read -s -p "请输入管理员密码: " ADMIN_PASS
echo ""

curl -X POST http://localhost/api/register \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$ADMIN_USER\",\"pass\":\"$ADMIN_PASS\"}" \
  && echo "✅ 管理员账号创建成功" \
  || echo "❌ 管理员账号创建失败"

echo ""
echo "🎉 部署完成！"
echo ""
echo "📋 服务信息："
echo "  - 项目目录: $PROJECT_DIR"
echo "  - 数据目录: $PROJECT_DIR/data"
echo "  - 配置文件: $PROJECT_DIR/.env.production"
echo ""
echo "🌐 访问地址："
echo "  - HTTP: http://localhost"
echo "  - HTTPS: https://localhost (自签名证书)"
echo ""
echo "📝 管理命令："
echo "  - 查看日志: cd $PROJECT_DIR && docker-compose logs -f"
echo "  - 重启服务: cd $PROJECT_DIR && docker-compose restart"
echo "  - 停止服务: cd $PROJECT_DIR && docker-compose down"
echo "  - 更新代码: cd $PROJECT_DIR && git pull && docker-compose build && docker-compose up -d"
echo ""
echo "⚠️  注意事项："
echo "  1. 请配置防火墙，只开放必要端口"
echo "  2. 建议配置 Cloudflare Tunnel 用于公网访问"
echo "  3. 定期备份 data 目录"
echo "  4. 监控系统资源使用情况"
