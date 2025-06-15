# main.py
import uvicorn
import requests
import os
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.security import APIKeyQuery, APIKeyHeader
from typing import List, Dict, Any

# --------------------------------------------------------------------------
# 1. 数据库、管理员设置、防爆破设置
# --------------------------------------------------------------------------
DB_FILE = "database.json"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

failed_attempts: Dict[str, List[datetime]] = {}
MAX_ATTEMPTS = 10
BLOCK_DURATION_MINUTES = 15
TIME_WINDOW_MINUTES = 5

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: json.dump({}, f)

def read_db() -> Dict[str, Any]:
    try:
        if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0: return {}
        with open(DB_FILE, 'r') as f: return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): return {}

def write_db(data: Dict[str, Any]):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

init_db()

# --------------------------------------------------------------------------
# 2. FastAPI 应用实例 和 CORS 配置
# --------------------------------------------------------------------------
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "false").lower() == "true"
app = FastAPI(title="我的IPTV聚合服务 (动态Token管理版)")

origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# 3. 认证设置 (核心改动：更可靠的IP获取方式)
# --------------------------------------------------------------------------
def get_client_ip(request: Request) -> str:
    """更可靠地获取客户端IP，优先信任反向代理设置的请求头"""
    if "x-forwarded-for" in request.headers:
        # X-Forwarded-For 可以是一个IP列表，第一个通常是真实的客户端IP
        return request.headers["x-forwarded-for"].split(',')[0].strip()
    # 如果没有代理头，则回退到直接连接的IP
    if request.client and request.client.host:
        return request.client.host
    return "unknown"

user_token_query = APIKeyQuery(name="token", auto_error=False)

def verify_user_token(token: str = Depends(user_token_query)):
    db = read_db()
    if not token or token not in db:
        raise HTTPException(status_code=403, detail="无效或缺失的用户令牌")
    db[token]["access_count"] += 1
    db[token]["last_access"] = datetime.utcnow().isoformat()
    write_db(db)
    return token

admin_token_header = APIKeyHeader(name="X-Admin-Token", auto_error=False)

def verify_admin_token(request: Request, token: str = Depends(admin_token_header)):
    client_ip = get_client_ip(request)
    now = datetime.utcnow()
    
    if client_ip in failed_attempts:
        failed_attempts[client_ip] = [t for t in failed_attempts[client_ip] if now - t < timedelta(minutes=TIME_WINDOW_MINUTES)]

    if client_ip in failed_attempts and len(failed_attempts[client_ip]) >= MAX_ATTEMPTS:
        last_attempt_time = failed_attempts[client_ip][-1]
        if now - last_attempt_time < timedelta(minutes=BLOCK_DURATION_MINUTES):
            raise HTTPException(status_code=429, detail=f"登录失败次数过多，请在 {BLOCK_DURATION_MINUTES} 分钟后重试。")
        else:
            failed_attempts.pop(client_ip, None)

    if not ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="服务未配置管理员令牌")
    
    if not token or token != ADMIN_TOKEN:
        if client_ip not in failed_attempts:
            failed_attempts[client_ip] = []
        failed_attempts[client_ip].append(now)
        raise HTTPException(status_code=403, detail="无效或缺失的管理员令牌")
    
    failed_attempts.pop(client_ip, None)
    return token

# --------------------------------------------------------------------------
# 4. 直播源数据
# --------------------------------------------------------------------------
PUBLIC_SOURCES = {"测试频道": [{"name": "4K测试-SDR", "logo": "https://cdn.jsdelivr.net/gh/feiyangdigital/testvideo/tg.jpg", "url": "https://cdn.jsdelivr.net/gh/feiyangdigital/testvideo/sdr4kvideo/index.m3u8"}]}
MIGU_SOURCES = {"央视频道 (代理)": [{"name": "CCTV1综合", "logo": "https://wapx.cmvideo.cn/publish/poms/image/2201/057/821/202204010054_1626677502161_H169_1080.jpg", "channel_id": "608807420"}]}

# --------------------------------------------------------------------------
# 5. API 路由
# --------------------------------------------------------------------------

# --- 用户接口 ---
@app.get("/tv.m3u", response_class=PlainTextResponse, dependencies=[Depends(verify_user_token)])
async def get_m3u_playlist(request: Request):
    host_header = request.headers['host']
    token = request.query_params.get('token')
    m3u_content = '#EXTM3U x-tvg-url="https://epg.v1.mk/fy.xml"\n\n'
    for group_title, channels in PUBLIC_SOURCES.items():
        for channel in channels:
            m3u_content += f'#EXTINF:-1 tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="{group_title}",{channel["name"]}\n'
            m3u_content += f'{channel["url"]}\n'
    if PROXY_ENABLED:
        for group_title, channels in MIGU_SOURCES.items():
            for channel in channels:
                proxy_url = f"http://{host_header}/proxy/migu/{channel['channel_id']}?token={token}"
                m3u_content += f'#EXTINF:-1 tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="{group_title}",{channel["name"]}\n'
                m3u_content += f'{proxy_url}\n'
    return PlainTextResponse(content=m3u_content)

if PROXY_ENABLED:
    @app.get("/proxy/migu/{channel_id}", dependencies=[Depends(verify_user_token)])
    async def proxy_migu_stream(channel_id: str):
        real_stream_url = f"http://live.miguvideo.com/wd_r/{channel_id}/L/1/0/0/index.m3u8"
        try:
            response = requests.get(real_stream_url, timeout=5, stream=True)
            response.raise_for_status()
            return Response(content=response.content, media_type="application/vnd.apple.mpegurl")
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"无法从源站获取视频流: {e}")

# --- 管理员接口 ---
@app.get("/admin/tokens", response_model=Dict[str, Any], dependencies=[Depends(verify_admin_token)])
async def list_tokens():
    return read_db()

# **核心修正：** 移除了 Body() 中的 embed=True，修复了创建单个用户的潜在bug
@app.post("/admin/tokens", response_model=Dict[str, Any], dependencies=[Depends(verify_admin_token)])
async def create_token(payload: Dict[str, str] = Body(...)):
    db = read_db()
    new_token = os.urandom(16).hex()
    description = payload.get("description", "No description")
    if new_token in db:
        raise HTTPException(status_code=400, detail="Token collision")
    db[new_token] = {"description": description, "created_at": datetime.utcnow().isoformat(), "last_access": None, "access_count": 0}
    write_db(db)
    return {"new_token": new_token, "details": db[new_token]}

@app.post("/admin/tokens/batch", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_admin_token)])
async def create_batch_tokens(payload: Dict[str, Any] = Body(...)):
    db = read_db()
    try:
        count = int(payload.get("count", 0))
        description_prefix = payload.get("description_prefix", "Batch-Generated")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="无效的输入，'count' 必须是一个数字。")
    if not (1 <= count <= 100):
        raise HTTPException(status_code=400, detail="'count' 必须在 1 到 100 之间。")
    newly_created_tokens = []
    for i in range(count):
        while True:
            new_token = os.urandom(16).hex()
            if new_token not in db: break 
        description = f"{description_prefix}-{i+1}"
        token_data = {"description": description, "created_at": datetime.utcnow().isoformat(), "last_access": None, "access_count": 0}
        db[new_token] = token_data
        newly_created_tokens.append({"token": new_token, "description": description})
    write_db(db)
    return newly_created_tokens

@app.delete("/admin/tokens/{token_to_delete}", response_model=Dict[str, str], dependencies=[Depends(verify_admin_token)])
async def delete_token(token_to_delete: str):
    db = read_db()
    if token_to_delete not in db:
        raise HTTPException(status_code=404, detail="Token not found")
    del db[token_to_delete]
    write_db(db)
    return {"message": "Token deleted", "deleted_token": token_to_delete}

# --- 健康检查 ---
@app.get("/", response_class=PlainTextResponse)
async def root():
    status = "已开启" if PROXY_ENABLED else "已关闭"
    return PlainTextResponse(f"欢迎来到我的IPTV聚合服务！\n代理模式当前: {status}")

# --- 本地测试启动 ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
