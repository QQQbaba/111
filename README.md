# 密码保护的静态内容网站

这是一个带密码保护的静态内容网站，适合托管大量媒体文件（图片、音频、视频等）。

## 功能特点

- 密码保护访问（密码: 220613）
- 支持大型媒体文件（共600MB）
- 基于Deno构建，易于部署
- 支持本地和云端运行

## 使用方法

### 本地运行

1. 安装 Deno: https://deno.land/#installation

2. 启动服务器：

```bash
deno run --allow-net --allow-read server.js
```

3. 在浏览器中访问: http://localhost:8000

### 部署到Deno Deploy

1. 在 [Deno Deploy](https://deno.com/deploy) 创建账号
2. 创建新项目
3. 上传本仓库内容
4. 设置入口点为 `server.js`

### 部署到Vercel

1. 安装Vercel CLI
2. 确保项目中包含`vercel.json`文件
3. 运行 `vercel`命令部署

## 项目结构

```
/
├── server.js        # Deno服务器文件
├── index.html       # 密码保护界面
├── 看抖音.html        # 主内容
├── deno.json        # Deno配置文件
├── image/           # 图片资源目录
├── music/           # 音频资源目录
├── video/           # 视频资源目录
└── ...其他资源目录
```

## 自定义密码

修改`server.js`文件中的`CORRECT_PASSWORD`变量来更改密码。 