# 硅基流动嵌入模型 API 代理服务

这个项目提供了一个简单的API代理服务，将OpenAI格式的嵌入请求转换为硅基流动(Silicon Flow)API格式。这允许您在需要兼容OpenAI API的应用程序中使用硅基流动的嵌入模型，如LobeChat知识库等。

## 功能

- 将OpenAI格式的嵌入请求转换为硅基流动API格式
- 将硅基流动API的响应转换回OpenAI格式
- 支持模型映射，自动将OpenAI模型名称转换为硅基流动模型名称
- 支持CORS，可以从浏览器中调用
- 轻量级设计，易于部署和维护
- 支持通过环境变量配置API密钥和模型映射

## 模型映射

目前支持以下模型映射：

| OpenAI模型名称 | 硅基流动模型名称 |
|--------------|--------------|
| text-embedding-3-small | BAAI/bge-m3 |
| text-embedding-3-large | BAAI/bge-m3 |
| text-embedding-ada-002 | BAAI/bge-large-zh-v1.5 |

## 本地开发

### 前提条件

- [Deno](https://deno.com/) 环境

### 安装步骤

1. 克隆仓库：
   ```bash
   git clone <仓库URL>
   cd api-proxy
   ```

2. 运行测试（可选）：
   ```bash
   deno run --allow-net test.ts
   ```

3. 启动本地服务器：
   ```bash
   deno run --allow-net --allow-env main.ts
   ```

4. 服务将在 http://localhost:8000 上运行

## 环境变量配置

服务支持以下环境变量来自定义行为：

| 环境变量 | 描述 | 默认值 |
|--------|------|-------|
| `SILICON_API_KEY` | 硅基流动API密钥 | 示例密钥 |
| `SILICON_API_ENDPOINT` | 硅基流动API端点 | https://api.siliconflow.cn/v1/embeddings |
| `CUSTOM_MODEL_MAPPING` | 自定义模型映射的JSON字符串 | 无 |

### 使用环境变量示例

本地运行时：

```bash
SILICON_API_KEY=your-api-key deno run --allow-net --allow-env main.ts
```

设置自定义模型映射：

```bash
SILICON_API_KEY=your-api-key CUSTOM_MODEL_MAPPING='{"text-embedding-3-medium":"BAAI/bge-base-zh-v1.5"}' deno run --allow-net --allow-env main.ts
```

## 部署到Deno Deploy

### 方法1：使用Deno Deploy Dashboard

1. 注册[Deno Deploy](https://deno.com/deploy)账号并登录
2. 创建新项目
3. 选择"从GitHub部署"
4. 连接您的GitHub仓库
5. 选择包含代码的分支
6. 设置入口文件为 `deploy.ts`
7. 在项目设置中配置环境变量（如`SILICON_API_KEY`）
8. 点击部署

### 方法2：使用Deno Deploy CLI

1. 安装Deno Deploy CLI:
   ```bash
   deno install --allow-read --allow-write --allow-env --allow-net --allow-run --no-check -r -f https://deno.land/x/deploy/deployctl.ts
   ```

2. 登录Deno Deploy账号:
   ```bash
   deployctl login
   ```

3. 部署服务:
   ```bash
   deployctl deploy --project=<your-project-name> --env=SILICON_API_KEY=<your-api-key> deploy.ts
   ```

### 方法3：通过GitHub Actions自动部署

1. 在GitHub仓库中设置一个Deno Deploy密钥
2. 在GitHub仓库设置中添加环境变量（如`SILICON_API_KEY`）
3. 创建`.github/workflows/deploy.yml`文件，内容如下:

```yaml
name: Deploy
on: [push]

jobs:
  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    
    steps:
      - name: Clone repository
        uses: actions/checkout@v3

      - name: Deploy to Deno Deploy
        uses: denoland/deployctl@v1
        with:
          project: <your-project-name>
          entrypoint: deploy.ts
          env-vars: |
            SILICON_API_KEY=${{ secrets.SILICON_API_KEY }}
```

### 验证部署

部署完成后，您可以使用测试脚本验证服务是否正常运行：

```bash
deno run --allow-net test.ts remote url=https://your-project.deno.dev
```

## 在LobeChat中使用

1. 打开LobeChat的"知识库"页面
2. 点击"知识库设置"
3. 在"嵌入模型提供商"中选择"OpenAI"
4. 在"API密钥"中输入任意值（代理服务不验证此值）
5. 在"API代理"中输入您部署的Deno服务URL，例如：`https://your-project.deno.dev`
6. 在"嵌入模型"中选择`text-embedding-3-small`
7. 点击"保存"

## 自定义配置

除了使用环境变量，您也可以直接修改`main.ts`文件来自定义配置：

```typescript
// 硅基流动API密钥
const SILICON_API_KEY = "你的API密钥";

// OpenAI兼容的模型映射
const DEFAULT_MODEL_MAPPING: Record<string, string> = {
  "text-embedding-3-small": "BAAI/bge-m3",
  // 添加更多模型映射
};
```

## 安全注意事项

在生产环境中，强烈建议通过环境变量配置API密钥，而不是将其硬编码在代码中。Deno Deploy提供了安全的环境变量存储。

此代理服务不执行任何认证，任何人都可以调用您部署的API端点。在生产环境中，建议添加某种形式的身份验证或访问控制。

## 故障排除

### API返回500错误

可能是硅基流动API密钥无效或已过期。检查API密钥并确保它有效。

### 模型不受支持错误

检查`MODEL_MAPPING`或环境变量中的模型映射是否包含您尝试使用的模型。如果没有，请添加适当的映射。

### CORS错误

如果从浏览器中调用API时遇到CORS错误，请确保`corsHeaders`函数返回所需的所有头部。

### 查看运行状态和配置

访问您部署的API根路径（如`https://your-project.deno.dev/`）可以查看服务的健康状态、当前使用的API端点和映射模型数量。

## 许可证

MIT 