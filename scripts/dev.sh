#!/bin/bash

# 网络自习室开发脚本
# 用于快速启动开发环境

set -e

echo "🚀 启动网络自习室开发环境..."

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查 docker-compose 是否存在
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose 未安装"
    exit 1
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data/redis

# 拉取必要的镜像
echo "📦 拉取 Docker 镜像..."
docker-compose pull redis guacd tomcat

# 构建自定义镜像
echo "🔨 构建应用镜像..."
docker-compose build

# 启动服务
echo "🎯 启动服务..."
docker-compose up -d redis

# 等待 Redis 启动
echo "⏳ 等待 Redis 启动..."
sleep 5

# 启动其他服务
docker-compose up -d

echo "✅ 服务启动完成！"
echo ""
echo "📋 服务状态："
docker-compose ps

echo ""
echo "🌐 访问地址："
echo "  - 前端: https://localhost (需要接受自签名证书)"
echo "  - 后端 API: http://localhost:8000"
echo "  - 聊天服务: http://localhost:7000"
echo ""
echo "📝 查看日志："
echo "  docker-compose logs -f [service_name]"
echo ""
echo "🛑 停止服务："
echo "  docker-compose down"
