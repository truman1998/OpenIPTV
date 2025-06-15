import uvicorn
import os
import requests
from fastapi import FastAPI, Request, Response, HTTPException

# --- 从环境变量读取配置 ---
# 你的中央服务器地址
CENTRAL_HUB_URL = os.getenv("CENTRAL_HUB_URL")
# 你在管理后台为这位用户创建的专属Token
USER_TOKEN = os.getenv("USER_TOKEN")

# --- FastAPI 应用实例 ---
app = FastAPI(title="IPTV Central Hub Client")

@app.get("/{full_path:path}")
async def forward_request(full_path: str, request: Request):
    if not CENTRAL_HUB_URL or not USER_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="服务未正确配置 (Client not configured: HUB URL or USER TOKEN is missing)"
        )

    # 构造要转发到中央服务器的完整URL
    target_url = f"{CENTRAL_HUB_URL}/{full_path}?token={USER_TOKEN}"
    
    print(f"Forwarding request to: {target_url}")

    try:
        # 发起请求到中央服务器
        response = requests.get(target_url, timeout=10, stream=True)
        response.raise_for_status()

        # 将中央服务器返回的内容原封不动地返回给用户的播放器
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"无法连接到中央服务器: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

```dockerfile
