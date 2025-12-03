"""
Project Sol: Pydantic Models for CTF Mission Generation (Ver 11.0)

Structured data models for Gemini API structured output.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class VulnerabilityInfo(BaseModel):
    """脆弱性情報"""
    cve_id: str = Field(..., description="CVE ID (例: CVE-2024-1234)")
    cvss: float = Field(..., ge=0.0, le=10.0, description="CVSSスコア (0.0-10.0)")
    attack_vector: str = Field(..., description="攻撃ベクトル (Network/Local/Adjacent Network/Physical)")


class DifficultyFactors(BaseModel):
    """難易度要因"""
    tech: int = Field(..., ge=1, le=5, description="技術的難易度 (1-5)")
    read: int = Field(..., ge=1, le=5, description="読解難易度 (1-5)")
    explore: int = Field(..., ge=1, le=5, description="探索難易度 (1-5)")


class EnvironmentInfo(BaseModel):
    """環境情報"""
    image: str = Field(..., description="Dockerイメージ名 (例: sol/mission-xxx:latest)")
    base_image: str = Field(..., description="ベースイメージ (python:3.11-slim または alpine:3.19)")
    cost_token: int = Field(..., ge=1000, le=10000, description="推定トークンコスト (1000-10000)")
    expected_solve_time: str = Field(..., description="期待される解答時間 (30m/45m/60m/90m/120m)")
    tags: List[str] = Field(..., description="タグリスト")


class NarrativeInfo(BaseModel):
    """ストーリー情報"""
    story_hook: str = Field(..., max_length=500, description="ストーリーフック（最大3文、禁止用語なし）")
    tone: str = Field(default="combat", description="トーン（常にcombat）")


class FileContent(BaseModel):
    """ファイルコンテンツ"""
    app_py: str = Field(..., alias="app.py", description="脆弱なアプリケーションコード（Python/Flask）")
    dockerfile: str = Field(..., alias="Dockerfile", description="Dockerfileの内容")
    requirements_txt: Optional[str] = Field(None, alias="requirements.txt", description="依存パッケージ（必要な場合）")
    flag_txt: Optional[str] = Field(None, alias="flag.txt", description="フラグファイル（オプション）")


class CTFMission(BaseModel):
    """CTF問題の完全なデータモデル"""
    mission_id: str = Field(..., pattern=r"^SOL-MSN-[A-Z0-9]{4}$", description="ミッションID (例: SOL-MSN-A1B2)")
    mission_version: str = Field(default="1.0.0", description="ミッションバージョン（常に1.0.0）")
    type: str = Field(..., description="問題タイプ (RCE/SQLi/SSRF/XXE/IDOR/PrivEsc/LogicError/Misconfig)")
    difficulty: int = Field(..., ge=1, le=5, description="難易度 (1-5)")
    difficulty_factors: DifficultyFactors = Field(..., description="難易度要因")
    vulnerability: VulnerabilityInfo = Field(..., description="脆弱性情報")
    environment: EnvironmentInfo = Field(..., description="環境情報")
    narrative: NarrativeInfo = Field(..., description="ストーリー情報")
    flag_answer: str = Field(..., pattern=r"^SolCTF\{.+\}$", description="フラグ (SolCTF{...}形式)")
    files: FileContent = Field(..., description="ファイルコンテンツ")
    writeup: str = Field(..., description="解説（Markdown形式）")
    tags: List[str] = Field(..., description="タグリスト")
    status: str = Field(default="draft", description="ステータス（常にdraft）")

    class Config:
        populate_by_name = True  # aliasと通常のフィールド名の両方を受け入れる
    
    def to_json_dict(self) -> Dict[str, Any]:
        """JSON形式に変換（ファイル名を元に戻す）"""
        result = self.model_dump(by_alias=False)
        if "files" in result:
            files = result["files"]
            if "app_py" in files:
                files["app.py"] = files.pop("app_py")
            if "dockerfile" in files:
                files["Dockerfile"] = files.pop("dockerfile")
            if "requirements_txt" in files:
                files["requirements.txt"] = files.pop("requirements_txt")
            if "flag_txt" in files:
                files["flag.txt"] = files.pop("flag_txt")
        return result

