# 网络自习室 (Study Room)

基于浏览器的 Linux 桌面自习环境，支持最多 50 名同时在线的学生。

## 功能特点

- 每位用户独占一台 Ubuntu + Xfce 容器
- 实时旁观其他用户桌面（只读）
- 内置聊天室功能
- 自动资源回收机制
- 单域名、单端口部署

## 技术架构

- **前端**: Vue 3 + Vite
- **后端**: FastAPI + SQLite
- **聊天**: Socket.IO + Node.js
- **桌面**: Apache Guacamole + VNC
- **容器**: Docker + Ubuntu Desktop
- **代理**: Nginx + Cloudflare Tunnel

## 快速开始

### 方式一：开发环境

```bash
# 克隆项目
git clone https://github.com/webwww123/111.git
cd 111

# 构建前端
./scripts/build.sh

# 启动开发环境
./scripts/dev.sh
```

### 方式二：生产部署

```bash
# 克隆项目
git clone https://github.com/webwww123/111.git
cd 111

# 运行部署脚本（自动安装依赖）
./scripts/deploy.sh
```

### 方式三：手动部署

#### 1. 环境准备

```bash
# 安装依赖
sudo apt update
sudo apt install -y docker.io docker-compose lxcfs

# 启动 lxcfs (用于隐藏容器硬件信息)
sudo systemctl enable --now lxcfs
```

#### 2. 构建应用

```bash
# 构建前端
cd frontend
npm install
npm run build
cd ..

# 创建数据目录
mkdir -p data/redis
```

#### 3. 启动服务

```bash
# 构建并启动服务
docker-compose build
docker-compose up -d

# 查看服务状态
docker-compose ps
```

#### 4. 创建管理员账号

```bash
curl -X POST http://localhost/api/register \
  -H "Content-Type: application/json" \
  -d '{"name":"admin","pass":"your-password"}'
```

## 配置 Cloudflare Tunnel (可选)

用于将内网服务安全地暴露到公网：

```bash
# 安装 cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# 创建隧道
cloudflared tunnel create studyroom
cloudflared tunnel route dns studyroom study.example.com
cloudflared tunnel run --url https://localhost:443
```

## 使用说明

### 学生使用流程

1. 访问网站并注册/登录账号
2. 点击"创建学习桌面"按钮
3. 等待桌面容器创建完成
4. 在自己的桌面中进行学习
5. 可以观看其他同学的桌面（只读）
6. 使用聊天室与其他同学交流
7. 学习结束后点击"结束学习"

### 管理员功能

- 查看所有在线用户
- 监控系统资源使用
- 管理用户会话

## 开发说明

详细的开发指南请参考 `开发指南` 文件。

### 项目结构

```
├── backend/          # FastAPI 后端服务
├── chat/            # Socket.IO 聊天服务
├── frontend/        # Vue 3 前端应用
├── manager/         # 容器管理服务
├── nginx/           # Nginx 配置
├── scripts/         # 部署和构建脚本
├── data/            # 数据存储目录
└── docker-compose.yml
```

### 开发环境

```bash
# 启动开发环境
./scripts/dev.sh

# 查看日志
docker-compose logs -f [service_name]

# 重启服务
docker-compose restart [service_name]

# 停止服务
docker-compose down
```

## 资源限制

- 每个用户容器: 1 GiB RAM / 0.5 vCPU
- 最大同时在线: 50 用户
- 无操作自动回收: 10 分钟

## 许可证

MIT License
