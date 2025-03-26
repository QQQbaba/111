// 测试硅基流动API和代理API的脚本

// 测试直接访问硅基流动API
async function testSiliconAPI() {
  console.log("测试直接访问硅基流动API...");
  
  try {
    const response = await fetch("https://api.siliconflow.cn/v1/embeddings", {
      method: "POST",
      headers: {
        "Authorization": "Bearer sk-guaaldyqlkmplbzziptbktjdepkypvebfghokjrovaykpqos",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "BAAI/bge-m3",
        input: "这是一个测试输入",
        encoding_format: "float"
      }),
    });
    
    console.log(`硅基流动API状态: ${response.status}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error("硅基流动API错误:", errorData);
      return false;
    }
    
    const data = await response.json();
    console.log("硅基流动API响应:", {
      model: data.model,
      "embedding维度": data.data[0].embedding.length,
      usage: data.usage
    });
    
    return true;
  } catch (error) {
    console.error("访问硅基流动API时出错:", error);
    return false;
  }
}

// 测试本地代理API
async function testLocalProxyAPI() {
  console.log("测试本地代理API...");
  
  try {
    const response = await fetch("http://localhost:8000/v1/embeddings", {
      method: "POST",
      headers: {
        "Authorization": "Bearer sk-dummy",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "text-embedding-3-small",
        input: "这是一个测试输入",
      }),
    });
    
    console.log(`本地代理API状态: ${response.status}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error("本地代理API错误:", errorData);
      return false;
    }
    
    const data = await response.json();
    console.log("本地代理API响应:", {
      model: data.model,
      "embedding维度": data.data[0].embedding.length,
      usage: data.usage
    });
    
    return true;
  } catch (error) {
    console.error("访问本地代理API时出错:", error);
    return false;
  }
}

// 测试远程部署的代理API
async function testDeployedProxyAPI(deployUrl: string) {
  console.log(`测试部署在 ${deployUrl} 的代理API...`);
  
  try {
    const response = await fetch(`${deployUrl}/v1/embeddings`, {
      method: "POST",
      headers: {
        "Authorization": "Bearer sk-dummy",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "text-embedding-3-small",
        input: "这是一个测试输入",
      }),
    });
    
    console.log(`远程代理API状态: ${response.status}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error("远程代理API错误:", errorData);
      return false;
    }
    
    const data = await response.json();
    console.log("远程代理API响应:", {
      model: data.model,
      "embedding维度": data.data[0].embedding.length,
      usage: data.usage
    });
    
    return true;
  } catch (error) {
    console.error("访问远程代理API时出错:", error);
    return false;
  }
}

// 运行测试
async function runTests() {
  // 首先测试硅基流动API
  const siliconSuccess = await testSiliconAPI();
  
  if (!siliconSuccess) {
    console.error("硅基流动API测试失败，请检查API密钥和连接。");
    return;
  }
  
  // 检查命令行参数
  const args = Deno.args;
  
  if (args.includes("local")) {
    console.log("\n请确保本地服务器已启动 (deno run --allow-net main.ts)");
    console.log("等待5秒后开始测试本地代理...");
    
    // 等待5秒以便用户启动服务器
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // 测试本地代理
    await testLocalProxyAPI();
  }
  
  if (args.includes("remote")) {
    // 获取部署URL参数
    const urlParam = args.find(arg => arg.startsWith("url="));
    if (urlParam) {
      const deployUrl = urlParam.split("=")[1];
      if (deployUrl) {
        // 测试远程部署的代理
        await testDeployedProxyAPI(deployUrl);
      } else {
        console.error("请提供有效的部署URL，例如: url=https://your-app.deno.dev");
      }
    } else {
      console.error("使用remote参数时必须提供部署URL，例如: url=https://your-app.deno.dev");
    }
  }
  
  if (!args.includes("local") && !args.includes("remote")) {
    console.log("\n运行测试指令:");
    console.log("- 本地测试: deno run --allow-net test.ts local");
    console.log("- 远程测试: deno run --allow-net test.ts remote url=https://your-app.deno.dev");
  }
}

// 执行测试
runTests(); 