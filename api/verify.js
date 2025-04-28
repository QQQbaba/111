// Vercel API函数，用于密码验证
export default async function handler(req, res) {
  // 只允许POST请求
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, message: '方法不允许' });
  }

  // 获取请求体
  try {
    const password = req.body.password;
    const correctPassword = '220613';

    if (password === correctPassword) {
      // 设置会话cookie
      const sessionId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
      
      // 设置cookie，1天有效期
      res.setHeader('Set-Cookie', `session=${sessionId}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400`);
      
      return res.status(200).json({ success: true });
    } else {
      return res.status(401).json({ success: false, message: '密码错误' });
    }
  } catch (error) {
    return res.status(400).json({ success: false, message: '请求格式错误' });
  }
} 