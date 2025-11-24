"""
Authentication dependencies for FastAPI
Supabase JWT検証とユーザー取得
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import os
import requests
from jose import jwt, JWTError
from typing import Optional

# Security scheme
security = HTTPBearer()

# Supabase client for JWT verification
def get_supabase_client() -> Client:
    """Supabaseクライアントを取得"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration missing"
        )
    
    return create_client(supabase_url, supabase_key)


def get_supabase_jwt_secret() -> str:
    """Supabase JWT Secretを取得（環境変数から）"""
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    if not jwt_secret:
        # JWT Secretが設定されていない場合、Supabase URLから取得を試みる
        # 実際の運用では、環境変数で設定することを推奨
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET not configured"
        )
    return jwt_secret


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    JWTトークンを検証してユーザー情報を取得
    
    Args:
        credentials: HTTP Bearerトークン
    
    Returns:
        dict: ユーザー情報 (id, email等)
    
    Raises:
        HTTPException: 認証失敗時
    """
    token = credentials.credentials
    
    try:
        # SupabaseのJWT Secretを取得
        # 注意: 実際の運用では、Supabaseの公開鍵を使って検証することを推奨
        # ここでは簡易的に、Supabase APIを使ってユーザー情報を取得
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase configuration missing"
            )
        
        # Supabase REST APIを使ってユーザー情報を取得
        # この方法は、JWTトークンが有効な場合にユーザー情報を返す
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": os.getenv("SUPABASE_ANON_KEY", ""),
        }
        
        response = requests.get(
            f"{supabase_url}/auth/v1/user",
            headers=headers,
            timeout=5
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_data = response.json()
        
        return {
            "id": user_data.get("id"),
            "email": user_data.get("email"),
            "user_metadata": user_data.get("user_metadata", {}),
        }
    
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

