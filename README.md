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

### 1. 环境准备

```bash
# 安装依赖
sudo apt update
sudo apt install -y docker.io docker-compose lxcfs

# 启动 lxcfs (用于隐藏容器硬件信息)
sudo systemctl enable --now lxcfs
```

### 2. 部署应用

```bash
# 克隆项目
git clone <repository-url>
cd studyroom

# 构建并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 3. 创建管理员账号

```bash
curl -X POST http://localhost/api/register \
  -H "Content-Type: application/json" \
  -d '{"name":"admin","pass":"your-password"}'
```

### 4. 配置 Cloudflare Tunnel (可选)

```bash
# 安装 cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# 创建隧道
cloudflared tunnel create studyroom
cloudflared tunnel route dns studyroom study.example.com
cloudflared tunnel run --url https://localhost:443
```

## 开发说明

详细的开发指南请参考 `开发指南` 文件。

## 资源限制

- 每个用户容器: 1 GiB RAM / 0.5 vCPU
- 最大同时在线: 50 用户
- 无操作自动回收: 10 分钟

## 许可证

MIT License
