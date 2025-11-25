from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import docker
import time
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.dependencies import get_current_user
from supabase import create_client, Client
from typing import Optional

# --- Configuration ---
app = FastAPI(title="Project Sol API")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Pydanticバリデーションエラーの詳細を返すハンドラー
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """422エラーの詳細を返す"""
    errors = exc.errors()
    error_details = []
    for error in errors:
        error_details.append({
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg"),
            "type": error.get("type")
        })
    
    print(f"[ERROR] Validation error: {error_details}")
    print(f"[ERROR] Request URL: {request.url}")
    print(f"[ERROR] Request method: {request.method}")
    
    # エラーメッセージを構築
    error_messages = [f"{err['field']}: {err['message']}" for err in error_details]
    detail_message = "; ".join(error_messages)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": detail_message,
            "errors": error_details,
            "message": "Request validation failed. Please check the request body."
        }
    )

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

# ctf_netネットワークの確保
def ensure_ctf_network():
    """ctf_netネットワークが存在することを確認し、なければ作成"""
    try:
        networks = client.networks.list(names=["ctf_net"])
        if not networks:
            print("[INFO] Creating ctf_net network (internal)")
            client.networks.create(
                name="ctf_net",
                driver="bridge",
                internal=True  # 外部インターネットアクセス不可
            )
            print("[SUCCESS] ctf_net network created")
        else:
            print("[INFO] ctf_net network already exists")
    except Exception as e:
        print(f"[WARNING] Failed to ensure ctf_net network: {str(e)}")
        # ネットワーク作成に失敗しても続行（既存のネットワークを使用）

# アプリケーション起動時にネットワークを確保
ensure_ctf_network()

# Supabase Client (Service Key for database access)
def get_supabase_db_client() -> Client:
    """Supabaseデータベースアクセス用クライアント（Service Key使用）"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_service_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase configuration missing (SUPABASE_URL or SUPABASE_SERVICE_KEY)"
        )
    
    return create_client(supabase_url, supabase_service_key)

# --- Schemas ---
class MissionStartRequest(BaseModel):
    challenge_id: str
    
    @field_validator('challenge_id')
    @classmethod
    def validate_challenge_id(cls, v):
        """challenge_idのバリデーション"""
        if not v or (isinstance(v, str) and v.strip() == ""):
            raise ValueError("challenge_id is required and cannot be empty")
        return str(v).strip()
    
    class Config:
        # フィールド名のエイリアスを許可
        populate_by_name = True

class MissionStartResponse(BaseModel):
    status: str
    container_id: str
    port: int
    url: str
    message: str
    challenge_name: Optional[str] = None

class ChallengeInfo(BaseModel):
    challenge_id: str  # APIレスポンスではchallenge_idとして返す
    title: str
    description: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    points: Optional[int] = None
    
    class Config:
        populate_by_name = True

class FlagSubmitRequest(BaseModel):
    challenge_id: str
    flag_submission: str
    
    @field_validator('challenge_id')
    @classmethod
    def validate_challenge_id(cls, v):
        """challenge_idのバリデーション"""
        if not v or (isinstance(v, str) and v.strip() == ""):
            raise ValueError("challenge_id is required and cannot be empty")
        return str(v).strip()
    
    @field_validator('flag_submission')
    @classmethod
    def validate_flag_submission(cls, v):
        """flag_submissionのバリデーション"""
        if not v or (isinstance(v, str) and v.strip() == ""):
            raise ValueError("flag_submission is required and cannot be empty")
        return str(v).strip()
    
    class Config:
        populate_by_name = True

class FlagSubmitResponse(BaseModel):
    correct: bool  # フロントエンドとの互換性のためcorrectに統一
    message: str
    challenge_id: str

# --- Routes ---

@app.get("/health")
def health_check():
    """監視用ヘルスチェック"""
    return {"status": "ok", "docker": "connected"}

@app.post("/api/containers/start", response_model=MissionStartResponse)
@limiter.limit("5/minute") # Rate Limit: 5回/分
def start_mission_container(
    mission_request: MissionStartRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    [Atomic Startup Strategy]
    1. challenge_idからSupabaseで問題情報を取得
    2. コンテナ起動 (Port 0 -> Random)
    3. Inspectでポート特定
    4. 成功なら情報を返す / 失敗なら完全削除
    
    Requires: Authentication (JWT Bearer Token)
    """
    user_id = current_user["id"]
    challenge_id = mission_request.challenge_id
    
    print(f"[INFO] Received mission start request: challenge_id={challenge_id}, user_id={user_id}")
    
    if not challenge_id or challenge_id.strip() == "":
        raise HTTPException(status_code=422, detail="challenge_id is required and cannot be empty")
    
    container = None
    
    try:
        # 1. Supabaseから問題情報を取得（flag_answerを含む）
        supabase = get_supabase_db_client()
        challenge_response = supabase.table("challenges").select("id, image_name, internal_port, title, flag_answer").eq("id", challenge_id).execute()
        
        if not challenge_response.data or len(challenge_response.data) == 0:
            raise HTTPException(status_code=404, detail=f"Challenge '{challenge_id}' not found")
        
        challenge = challenge_response.data[0]
        image_name = challenge.get("image_name")
        internal_port = challenge.get("internal_port", 8000)  # デフォルト8000
        challenge_title = challenge.get("title", challenge_id)
        flag_answer = challenge.get("flag_answer")  # DBからflag_answerを取得
        
        if not image_name:
            raise HTTPException(status_code=500, detail="Challenge image_name not configured")
        
        if not flag_answer:
            raise HTTPException(status_code=500, detail="Challenge flag_answer not configured")
        
        # ポートマッピングの動的解決
        # internal_portが設定されていればそれを使用、なければデフォルト値
        # Nginx系のイメージは80、Python/FastAPI系は8000が一般的
        port_mapping = {f'{internal_port}/tcp': ('0.0.0.0', 0)}
        
        # ネットワークの確認（起動時に作成済みだが、念のため再確認）
        try:
            networks = client.networks.list(names=["ctf_net"])
            if not networks:
                print("[WARNING] ctf_net network not found, creating...")
                ensure_ctf_network()
        except Exception as net_error:
            print(f"[WARNING] Network check failed: {net_error}")
        
        # 2. Port 0でコンテナ起動（Atomic Startup Strategy）
        try:
            container = client.containers.run(
                image_name,
                detach=True,
                ports=port_mapping,
                mem_limit="128m",
                nano_cpus=500000000,  # 0.5 CPU
                network="ctf_net",  # 隔離ネットワーク
                environment={
                    "CTF_FLAG": flag_answer  # DBから取得したflag_answerをコンテナに注入
                }
            )
            print(f"[INFO] Container {container.short_id} started successfully")
        except docker.errors.ImageNotFound as img_error:
            raise HTTPException(
                status_code=500,
                detail=f"Docker image '{image_name}' not found. Please build the image first."
            )
        except docker.errors.APIError as api_error:
            raise HTTPException(
                status_code=500,
                detail=f"Docker API error: {str(api_error)}"
            )
        
        # 3. ポート確認 (最大5回リトライ、1秒間隔)
        assigned_port = None
        max_retries = 5
        port_key = f'{internal_port}/tcp'
        
        for attempt in range(max_retries):
            container.reload()
            ports_dict = container.attrs.get('NetworkSettings', {}).get('Ports', {})
            
            # ポート情報が取得できるかチェック
            if port_key in ports_dict and ports_dict[port_key] and len(ports_dict[port_key]) > 0:
                assigned_port = ports_dict[port_key][0]['HostPort']
                break
            
            # 最後の試行でなければ待機
            if attempt < max_retries - 1:
                time.sleep(1)
        
        # ポート情報が取得できなかった場合
        if assigned_port is None:
            raise Exception(f"Failed to retrieve assigned port after {max_retries} retries")

        # TODO: ここでDBに {user_id, container_id, port, start_time, challenge_id} を保存する
        
        print(f"[SUCCESS] Container {container.short_id} started on port {assigned_port} for user {user_id} (challenge: {challenge_id})")

        return {
            "status": "success",
            "container_id": container.short_id,
            "port": int(assigned_port),
            "url": f"http://localhost:{assigned_port}",
            "message": "MISSION ENVIRONMENT DEPLOYED.",
            "challenge_name": challenge_title
        }

    except HTTPException:
        # HTTPExceptionはそのまま再発生
        if container:
            try:
                container.kill()
                container.remove()
                print("[ROLLBACK] Zombie container removed after HTTPException.")
            except:
                pass
        raise
    except docker.errors.DockerException as docker_error:
        error_msg = f"Docker error: {str(docker_error)}"
        print(f"[ERROR] {error_msg}")
        if container:
            try:
                container.kill()
                container.remove()
                print("[ROLLBACK] Zombie container removed.")
            except:
                pass
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Mission Start Failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        # [Self-Healing] 失敗時は即座にゴミ掃除 (Rollback)
        if container:
            try:
                container.kill()
                container.remove()
                print("[ROLLBACK] Zombie container removed.")
            except Exception as rollback_error:
                print(f"[WARNING] Rollback failed: {str(rollback_error)}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/challenges", response_model=list[ChallengeInfo])
def list_challenges(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    利用可能なCTF問題一覧を取得
    
    Requires: Authentication (JWT Bearer Token)
    
    Returns:
        list[ChallengeInfo]: 問題一覧（pointsの昇順でソート）
    """
    try:
        user_id = current_user.get("id", "unknown")
        print(f"[INFO] Fetching challenges for user: {user_id}")
        
        supabase = get_supabase_db_client()
        # 存在するカラムのみを取得（categoryカラムは存在しないため除外）
        # 実際のDBスキーマ: id, title, description, difficulty, points, image_name, internal_port, flag など
        response = supabase.table("challenges").select(
            "id, title, description, difficulty, points"
        ).execute()
        
        print(f"[INFO] Supabase response: {len(response.data) if response.data else 0} challenges found")
        
        if not response.data:
            print("[WARNING] No challenges found in database")
            return []
        
        # pointsの昇順でソート（None値は最後に配置）
        challenges = response.data
        challenges_sorted = sorted(
            challenges,
            key=lambda x: (x.get("points") is None, x.get("points") or 0)
        )
        
        # DBのidカラムをchallenge_idとしてマッピング
        result = []
        for challenge in challenges_sorted:
            challenge_data = {
                "challenge_id": challenge.get("id"),  # DBのidをchallenge_idとして設定
                "title": challenge.get("title", ""),
                "description": challenge.get("description"),
                "difficulty": challenge.get("difficulty"),
                "points": challenge.get("points"),
                "category": None,  # 存在しないカラムのため明示的にNone
            }
            challenge_info = ChallengeInfo(**challenge_data)
            result.append(challenge_info)
        print(f"[SUCCESS] Returning {len(result)} challenges")
        return result
    
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        error_msg = f"Failed to fetch challenges: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/challenges/submit", response_model=FlagSubmitResponse)
@limiter.limit("10/minute")  # Rate Limit: 10回/分（ブルートフォース対策）
def submit_flag(
    flag_request: FlagSubmitRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Flag提出と判定API
    
    Requires: Authentication (JWT Bearer Token)
    Rate Limit: 5 requests/minute
    
    Process:
    1. Supabaseのchallengesテーブルから正解Flagを取得
    2. 提出されたFlagと照合（直接比較、ハッシュ化なし）
    3. submission_logsテーブルに記録
    4. 結果を返す
    """
    user_id = current_user["id"]
    challenge_id = flag_request.challenge_id
    submitted_flag = flag_request.flag_submission
    
    print(f"[INFO] Flag submission: challenge_id={challenge_id}, user_id={user_id}")
    
    try:
        supabase = get_supabase_db_client()
        
        # 1. チャレンジ情報を取得（正解Flagを含む）
        # flag_answerカラムのみを取得（flagカラムは存在しないため削除）
        challenge_response = supabase.table("challenges").select("id, flag_answer").eq("id", challenge_id).execute()
        
        if not challenge_response.data or len(challenge_response.data) == 0:
            raise HTTPException(status_code=404, detail=f"Challenge '{challenge_id}' not found")
        
        challenge = challenge_response.data[0]
        
        # 2. 正解Flagを取得（flag_answerカラムから取得）
        correct_flag = challenge.get("flag_answer")
        
        if not correct_flag:
            raise HTTPException(
                status_code=500,
                detail="Correct flag not configured for this challenge (flag_answer column missing or empty)"
            )
        
        print(f"[INFO] Found correct flag for challenge_id={challenge_id}")
        
        # 3. Flag照合（直接比較、大文字小文字を区別）
        is_correct = (submitted_flag.strip() == correct_flag.strip())
        
        # 4. IPアドレスを取得
        client_ip = get_remote_address(request)
        
        # 5. submission_logsテーブルに記録
        try:
            log_data = {
                "user_id": user_id,
                "challenge_id": challenge_id,
                "submitted_flag": submitted_flag,  # 実際の運用ではハッシュ化推奨だが今回は生データ
                "is_correct": is_correct,
                "ip_address": client_ip
            }
            supabase.table("submission_logs").insert(log_data).execute()
            print(f"[INFO] Submission log recorded: is_correct={is_correct}")
        except Exception as log_error:
            # submission_logsテーブルが存在しない場合でも処理を続行
            print(f"[WARNING] Failed to log submission: {str(log_error)}")
            print("[INFO] Continuing without logging (table may not exist)")
        
        # 6. 結果を返す
        if is_correct:
            message = "MISSION ACCOMPLISHED. WELL DONE AGENT."
            print(f"[SUCCESS] User {user_id} submitted correct flag for challenge {challenge_id}")
        else:
            message = "INVALID FLAG. ACCESS DENIED."
            print(f"[INFO] User {user_id} submitted incorrect flag for challenge {challenge_id}")
        
        return {
            "correct": is_correct,  # フロントエンドとの互換性のためcorrectに統一
            "message": message,
            "challenge_id": challenge_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Flag submission failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/containers/stop")
@limiter.limit("5/minute")  # Rate Limit: 5回/分 (PROJECT_MASTER.md 4.4準拠)
def stop_container(
    container_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)  # 認証必須
):
    """
    コンテナ停止API
    
    Requires: Authentication (JWT Bearer Token)
    Rate Limit: 5 requests/minute
    """
    try:
        container = client.containers.get(container_id)
        container.kill()
        container.remove()
        return {"status": "deleted", "id": container_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Container not found")