// Deno服务器配置
import { serve } from "https://deno.land/std@0.192.0/http/server.ts";
import { serveFile } from "https://deno.land/std@0.192.0/http/file_server.ts";

const CORRECT_PASSWORD = "220613";
const PORT = 8000;

// 简单的session管理
const sessions = new Map();

function generateSessionId() {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

async function handler(req) {
  const url = new URL(req.url);
  const path = url.pathname;
  
  // 检查cookie中的会话
  const cookieHeader = req.headers.get("cookie") || "";
  const cookies = Object.fromEntries(
    cookieHeader.split(";").map(cookie => cookie.trim().split("=")).filter(parts => parts.length === 2)
  );
  
  const sessionId = cookies.session;
  const isAuthenticated = sessionId && sessions.has(sessionId);
  
  // 密码验证端点
  if (path === "/verify-password" && req.method === "POST") {
    try {
      const body = await req.json();
      if (body.password === CORRECT_PASSWORD) {
        const newSessionId = generateSessionId();
        sessions.set(newSessionId, { authenticated: true, createdAt: Date.now() });
        
        return new Response(JSON.stringify({ success: true }), {
          headers: {
            "Content-Type": "application/json",
            "Set-Cookie": `session=${newSessionId}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400`
          }
        });
      } else {
        return new Response(JSON.stringify({ success: false, message: "密码错误" }), {
          status: 401,
          headers: { "Content-Type": "application/json" }
        });
      }
    } catch (e) {
      return new Response(JSON.stringify({ success: false, message: "请求格式错误" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
  }
  
  // 清理过期会话（24小时）
  for (const [id, session] of sessions.entries()) {
    if (Date.now() - session.createdAt > 24 * 60 * 60 * 1000) {
      sessions.delete(id);
    }
  }
  
  // 对于根路径，总是提供登录页面
  if (path === "/" || path === "/index.html") {
    return await serveFile(req, "./index.html");
  }
  
  // 如果未认证，只允许访问index.html和静态资源中的css/js
  if (!isAuthenticated) {
    if (path.endsWith(".css") || path.endsWith(".js")) {
      try {
        return await serveFile(req, `.${path}`);
      } catch {
        return new Response("未找到", { status: 404 });
      }
    }
    
    // 重定向到登录页面
    return new Response("需要认证", {
      status: 302,
      headers: { "Location": "/" }
    });
  }
  
  // 已认证用户的静态文件服务
  try {
    // 路径安全检查，防止目录遍历
    const normalizedPath = path.replace(/\/\.{1,2}\//g, "/");
    const filePath = `.${normalizedPath}`;
    
    return await serveFile(req, filePath);
  } catch {
    return new Response("未找到", { status: 404 });
  }
}

console.log(`HTTP服务器启动在 http://localhost:${PORT}/`);
await serve(handler, { port: PORT }); 