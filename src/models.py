"""
CTF Challenge Generator Data Models

Pydanticモデル定義: CTF問題生成のためのデータ構造
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


# ============================================
# レガシー: クイズ生成モデル（コメントアウト）
# ============================================
# 
# class Option(BaseModel):
#     """クイズの選択肢"""
#     
#     model_config = ConfigDict(extra='ignore')
#     
#     text: str = Field(..., description="選択肢のテキスト")
#     is_correct: bool = Field(..., description="正解かどうか")
#     explanation: str = Field(..., description="選択肢の説明")
# 
# 
# class QuizQuestion(BaseModel):
#     """クイズの問題"""
#     
#     model_config = ConfigDict(extra='ignore')
#     
#     question_text: str = Field(..., description="問題文")
#     options: List[Option] = Field(..., description="選択肢のリスト（通常4つ）")
#     difficulty: int = Field(..., ge=1, le=5, description="難易度（1-5）")
#     tags: List[str] = Field(default_factory=list, description="タグ（例: ['セキュリティ', 'SQLi']）")
# 
# 
# class QuizSet(BaseModel):
#     """クイズセット（複数の問題）"""
#     
#     model_config = ConfigDict(extra='ignore')
#     
#     title: Optional[str] = Field(default=None, description="クイズセットのタイトル")
#     questions: List[QuizQuestion] = Field(..., description="問題のリスト")
# 
# 
# class QuizOutput(BaseModel):
#     """クイズ生成の出力"""
#     
#     model_config = ConfigDict(extra='ignore')
#     
#     quiz_set: QuizSet = Field(..., description="生成されたクイズセット")
#     context_used: str = Field(..., description="使用されたコンテキスト（要約）")
# ============================================


# ============================================
# CTF Challenge Models
# ============================================

class CTFChallenge(BaseModel):
    """CTF問題"""
    
    model_config = ConfigDict(extra='ignore')  # 予期しないフィールドを無視
    
    title: str = Field(..., description="問題のタイトル")
    description: str = Field(..., description="プレイヤーに表示する問題文")
    vulnerable_code: str = Field(..., description="脆弱性を含むPythonコード（Flaskなど）。1ファイルで完結させること。")
    flag: str = Field(..., description="SolCTF{...} 形式のフラグ")
    writeup: str = Field(..., description="Markdown形式の攻略解説。攻撃手法を具体的に記述。")
    difficulty: int = Field(..., ge=1, le=5, description="難易度 1-5")


class CTFOutput(BaseModel):
    """CTF問題生成の出力"""
    
    model_config = ConfigDict(extra='ignore')  # 予期しないフィールドを無視
    
    challenges: List[CTFChallenge] = Field(..., description="生成されたCTF問題のリスト")

