from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import docker
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.dependencies import get_current_user

# --- Configuration ---
app = FastAPI(title="Project Sol API")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS (Frontendからのアクセス許可)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker Client
client = docker.from_env()

# --- Schemas ---
class MissionStartResponse(BaseModel):
    status: str
    container_id: str
    port: int
    url: str
    message: str

# --- Routes ---

@app.get("/health")
def health_check():
    """監視用ヘルスチェック"""
    return {"status": "ok", "docker": "connected"}

@app.post("/api/containers/start", response_model=MissionStartResponse)
@limiter.limit("5/minute") # Rate Limit: 5回/分
def start_mission_container(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    [Atomic Startup Strategy]
    1. コンテナ起動 (Port 0 -> Random)
    2. Inspectでポート特定
    3. 成功なら情報を返す / 失敗なら完全削除
    
    Requires: Authentication (JWT Bearer Token)
    """
    user_id = current_user["id"]
    container = None
    try:
        # 1. Port 0でコンテナ起動 (テスト用に軽量なNginxを使用)
        # 本番では 'ctf_challenge_01' などの専用イメージを使う
        container = client.containers.run(
            "nginx:alpine", 
            detach=True,
            ports={'80/tcp': ('0.0.0.0', 0)}, # Port 0 = ランダム割り当て
            mem_limit="128m",
            nano_cpus=500000000, # 0.5 CPU
            network="ctf_net" # 隔離ネットワーク
        )
        
        # 2. ポート確認 (最大5回リトライ、1秒間隔)
        assigned_port = None
        max_retries = 5
        for attempt in range(max_retries):
            container.reload()
            ports_dict = container.attrs.get('NetworkSettings', {}).get('Ports', {})
            
            # ポート情報が取得できるかチェック
            if '80/tcp' in ports_dict and ports_dict['80/tcp'] and len(ports_dict['80/tcp']) > 0:
                assigned_port = ports_dict['80/tcp'][0]['HostPort']
                break
            
            # 最後の試行でなければ待機
            if attempt < max_retries - 1:
                time.sleep(1)
        
        # ポート情報が取得できなかった場合
        if assigned_port is None:
            raise Exception("Failed to retrieve assigned port after 5 retries")

        # TODO: ここでDBに {user_id, container_id, port, start_time} を保存する
        
        print(f"[SUCCESS] Container {container.short_id} started on port {assigned_port} for user {user_id}")

        return {
            "status": "success",
            "container_id": container.short_id,
            "port": int(assigned_port),
            "url": f"http://localhost:{assigned_port}",
            "message": "MISSION ENVIRONMENT DEPLOYED."
        }

    except Exception as e:
        print(f"[ERROR] Startup failed: {str(e)}")
        # [Self-Healing] 失敗時は即座にゴミ掃除 (Rollback)
        if container:
            try:
                container.kill()
                container.remove()
                print("[ROLLBACK] Zombie container removed.")
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Mission Start Failed: {str(e)}")

@app.post("/api/containers/stop")
def stop_container(container_id: str):
    """デバッグ用: 手動停止API"""
    try:
        container = client.containers.get(container_id)
        container.kill()
        container.remove()
        return {"status": "deleted", "id": container_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Container not found")