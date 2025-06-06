#!/bin/bash

# 网络自习室构建脚本

set -e

echo "🔨 开始构建网络自习室..."

# 检查 Node.js 是否安装
if ! command -v node > /dev/null 2>&1; then
    echo "❌ Node.js 未安装，请先安装 Node.js 18+"
    exit 1
fi

# 检查 npm 是否安装
if ! command -v npm > /dev/null 2>&1; then
    echo "❌ npm 未安装"
    exit 1
fi

# 构建前端
echo "📦 构建前端..."
cd frontend

# 安装依赖
echo "📥 安装前端依赖..."
npm install

# 构建
echo "🔨 构建前端应用..."
npm run build

# 检查构建结果
if [ ! -d "dist" ]; then
    echo "❌ 前端构建失败"
    exit 1
fi

echo "✅ 前端构建完成"

# 返回根目录
cd ..

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data/redis

# 设置权限
chmod 755 data

echo "✅ 构建完成！"
echo ""
echo "📋 构建结果："
echo "  - 前端: frontend/dist/"
echo "  - 数据目录: data/"
echo ""
echo "🚀 启动服务："
echo "  ./scripts/dev.sh"
