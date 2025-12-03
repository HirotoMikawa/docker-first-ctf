"""
CTF Challenge Generator

Gemini 2.0 Flash APIを使用してCTF問題を生成するクラス
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from google.api_core import exceptions as google_exceptions

from src.models import CTFOutput, CTFChallenge

# 環境変数を読み込む
load_dotenv()


class CTFChallengeGenerator:
    """
    CTF問題生成クラス
    
    Gemini 2.0 Flash APIを使用して、与えられたテキスト（脆弱性の解説など）から
    CTF問題を自動生成します。
    
    Attributes:
        model: Gemini 2.0 Flashモデルインスタンス
        api_key: Gemini APIキー
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: Gemini APIキー（Noneの場合は環境変数から取得）
        """
        # 環境変数からAPIキーを取得（GEMINI_API_KEYまたはGOOGLE_API_KEY）
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "APIキーが設定されていません。"
                ".envファイルにGEMINI_API_KEYまたはGOOGLE_API_KEYを設定するか、"
                "引数でapi_keyを指定してください。"
            )
        
        # Gemini APIを設定
        genai.configure(api_key=self.api_key)
        
        # Gemini 2.0 Flashモデルを初期化
        # response_schemaは使わず、プロンプトでJSON形式を指定する方法を使用
        # （Gemini APIが一部のJSONスキーマフィールドをサポートしていないため）
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.7,
            }
        )
    
    
    def _build_prompt(self, context: str, num_challenges: int = 1) -> str:
        """
        プロンプトを構築
        
        Args:
            context: CTF問題生成の元となるテキスト（脆弱性の解説など）
            num_challenges: 生成する問題数
        
        Returns:
            構築されたプロンプト
        """
        prompt = f"""以下のテキストを基に、CTF（Capture The Flag）問題を生成してください。

【テキスト】
{context}

【要件】
1. {num_challenges}個のCTF問題を生成してください
2. 入力されたテキストの内容に基づき、その脆弱性を再現するPythonコード（Flaskアプリなど）を作成してください
3. 脆弱なコードは1ファイルで完結させてください（app.pyなど）
4. フラグは必ず「SolCTF{{...}}」形式で生成してください
5. 攻略解説（Writeup）はMarkdown形式で、攻撃手法を具体的に記述してください
6. 難易度は1-5の範囲で適切に設定してください

【出力形式】
以下のJSON形式で出力してください。JSON以外のテキストは含めないでください。

{{
  "challenges": [
    {{
      "title": "問題のタイトル",
      "description": "プレイヤーに表示する問題文（脆弱性の種類や目標を説明）",
      "vulnerable_code": "脆弱性を含むPythonコード（Flaskなど）。1ファイルで完結させること。",
      "flag": "SolCTF{{example_flag}}",
      "writeup": "# 攻略解説\\n\\n## 脆弱性の種類\\n\\n...\\n\\n## 攻撃手順\\n\\n1. ...\\n2. ...",
      "difficulty": 3
    }}
  ]
}}

重要: 
- vulnerable_codeは実行可能な完全なPythonコードであること
- flagは必ず「SolCTF{{...}}」形式であること
- writeupはMarkdown形式で、具体的な攻撃手順を含めること
- 必ず有効なJSON形式で出力すること
"""
        return prompt
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type(google_exceptions.ResourceExhausted)
    )
    def generate_challenge(
        self,
        context: str,
        num_challenges: int = 1
    ) -> CTFOutput:
        """
        CTF問題を生成
        
        Args:
            context: CTF問題生成の元となるテキスト（脆弱性の解説など）
            num_challenges: 生成する問題数（デフォルト: 1）
        
        Returns:
            CTFOutput: 生成されたCTF問題
        
        Raises:
            ValueError: コンテキストが空の場合
            Exception: API呼び出しが失敗した場合
        """
        if not context or not context.strip():
            raise ValueError("コンテキストが空です。テキストを入力してください。")
        
        # プロンプトを構築
        prompt = self._build_prompt(context, num_challenges)
        
        # Gemini APIを呼び出し
        try:
            response = self.model.generate_content(prompt)
            
            # JSONレスポンスをパース
            response_text = response.text.strip()
            
            # JSONの前後のマークダウン記号を除去（もしあれば）
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # JSONをパースしてPydanticモデルに変換
            data = json.loads(response_text)
            ctf_output = CTFOutput(**data)
            
            return ctf_output
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSONのパースに失敗しました: {e}\nレスポンス: {response_text}")
        except Exception as e:
            raise Exception(f"CTF問題生成に失敗しました: {e}")

