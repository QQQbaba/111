import { serve } from "https://deno.land/std@0.216.0/http/server.ts";

// 从环境变量获取硅基流动API密钥，如果没有则使用默认值
const SILICON_API_KEY = Deno.env.get("SILICON_API_KEY") || "sk-guaaldyqlkmplbzziptbktjdepkypvebfghokjrovaykpqos";

// 允许自定义模型映射
const DEFAULT_MODEL_MAPPING: Record<string, string> = {
  "text-embedding-3-small": "BAAI/bge-m3", // 默认映射
  "text-embedding-3-large": "BAAI/bge-m3",
  "text-embedding-ada-002": "BAAI/bge-large-zh-v1.5",
};

// 如果环境变量中有自定义映射，则使用它们
const customMapping = Deno.env.get("CUSTOM_MODEL_MAPPING");
const MODEL_MAPPING = customMapping 
  ? { ...DEFAULT_MODEL_MAPPING, ...JSON.parse(customMapping) } 
  : DEFAULT_MODEL_MAPPING;

// 硅基流动API端点，允许自定义
const SILICON_API_ENDPOINT = Deno.env.get("SILICON_API_ENDPOINT") || "https://api.siliconflow.cn/v1/embeddings";

// 处理CORS请求的headers
function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
  };
}

// 处理预检请求
function handleOptions(request: Request) {
  return new Response(null, {
    status: 204,
    headers: {
      ...corsHeaders(),
      "Access-Control-Max-Age": "86400",
    },
  });
}

// 处理embedding请求
async function handleEmbeddings(request: Request) {
  try {
    // 从请求中获取JSON数据
    const requestData = await request.json();
    
    // 获取OpenAI的请求模型
    const openaiModel = requestData.model || "text-embedding-3-small";
    
    // 映射到硅基流动的模型
    const siliconModel = MODEL_MAPPING[openaiModel] || "BAAI/bge-m3";
    
    // 构建发送到硅基流动的请求
    const siliconRequest = {
      model: siliconModel,
      input: requestData.input,
      encoding_format: "float"
    };
    
    // 发送请求到硅基流动API
    const response = await fetch(SILICON_API_ENDPOINT, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${SILICON_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(siliconRequest),
    });
    
    // 获取硅基流动的响应
    const siliconResponse = await response.json();
    
    // 如果是错误响应
    if (!response.ok) {
      console.error("硅基流动API错误:", siliconResponse);
      return new Response(JSON.stringify({
        error: {
          message: `硅基流动API错误: ${siliconResponse.error?.message || "未知错误"}`,
          type: "api_error",
        }
      }), {
        status: response.status,
        headers: {
          ...corsHeaders(),
          "Content-Type": "application/json",
        },
      });
    }
    
    // 将硅基流动响应转换为OpenAI格式
    const openaiResponse = {
      object: "list",
      data: siliconResponse.data.map((item: any) => ({
        object: "embedding",
        embedding: item.embedding,
        index: item.index,
      })),
      model: openaiModel,
      usage: siliconResponse.usage,
    };
    
    // 返回OpenAI格式的响应
    return new Response(JSON.stringify(openaiResponse), {
      headers: {
        ...corsHeaders(),
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    console.error("处理请求时出错:", error);
    return new Response(JSON.stringify({
      error: {
        message: `服务器处理错误: ${error instanceof Error ? error.message : String(error)}`,
        type: "server_error",
      }
    }), {
      status: 500,
      headers: {
        ...corsHeaders(),
        "Content-Type": "application/json",
      },
    });
  }
}

// 主处理函数
async function handler(request: Request): Promise<Response> {
  // 处理预检请求
  if (request.method === "OPTIONS") {
    return handleOptions(request);
  }
  
  const url = new URL(request.url);
  
  // 处理健康检查
  if (url.pathname === "/health" || url.pathname === "/") {
    return new Response(JSON.stringify({ 
      status: "healthy",
      message: "硅基流动嵌入模型API代理服务正常运行中",
      version: "1.0.0",
      endpoint: SILICON_API_ENDPOINT,
      modelMappings: Object.keys(MODEL_MAPPING).length,
    }), {
      headers: {
        ...corsHeaders(),
        "Content-Type": "application/json",
      },
    });
  }
  
  // 处理v1/embeddings端点
  if (url.pathname === "/v1/embeddings") {
    return handleEmbeddings(request);
  }
  
  // 其他端点返回404
  return new Response(JSON.stringify({ 
    error: "Not Found",
    message: "API端点不存在，请使用 /v1/embeddings"
  }), {
    status: 404,
    headers: {
      ...corsHeaders(),
      "Content-Type": "application/json",
    },
  });
}

// 为Deno Deploy导出handler
serve(handler); 