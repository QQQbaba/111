// 中间件，保护内容访问
export default function middleware(req) {
  // 获取路径
  const url = new URL(req.url);
  const path = url.pathname;
  
  // 允许访问的路径
  const allowedPaths = [
    '/',
    '/index.html',
    '/verify-password',
    '/api/verify.js'
  ];
  
  // 允许访问的静态资源后缀
  const allowedExtensions = [
    '.css',
    '.js',
    '.ico',
    '.png',
    '.svg'
  ];
  
  // 检查是否是允许的路径或静态资源
  const isAllowedPath = allowedPaths.includes(path);
  const isAllowedExtension = allowedExtensions.some(ext => path.endsWith(ext));
  
  if (isAllowedPath || isAllowedExtension) {
    return;
  }
  
  // 检查cookie
  const cookies = req.cookies;
  const hasSession = cookies && cookies.session;
  
  // 如果没有会话，重定向到首页
  if (!hasSession) {
    return Response.redirect(new URL('/', req.url));
  }
} 