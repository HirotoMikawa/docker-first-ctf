"""
Project Sol: LLM-as-a-Judge Evaluator (Ver 11.0)

Quality assurance using Gemini API to evaluate generated CTF missions.
"""

import json
import os
from typing import Dict, Any, Tuple, Optional
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

# Google Gemini API
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    print("Error: google-generativeai library not installed.", file=sys.stderr)
    sys.exit(1)

# Load .env file
load_dotenv()


class MissionEvaluator:
    """
    LLM-as-a-Judgeによる問題品質評価器
    
    生成されたCTF問題の品質を自動評価し、基準を満たさない場合は
    フィードバックを提供して再生成を促す。
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: Gemini APIキー（Noneの場合は環境変数から読み込み）
        """
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable or api_key parameter is required")
        
        genai.configure(api_key=api_key)
        
        # Gemini 1.5 Flashモデル（評価用）
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
    
    def evaluate(self, mission_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        問題の品質を評価
        
        Args:
            mission_data: 評価対象のミッションデータ
            
        Returns:
            (score, feedback_dict)
            - score: 総合スコア (0-100)
            - feedback_dict: 詳細なフィードバック
        """
        evaluation_prompt = f"""あなたはCTF問題の品質評価専門家です。
以下のCTF問題の品質を評価してください。

**評価基準:**
1. 正確性 (Correctness) - 40%
   - 元の仕様に基づき、正しく動作するか
   - ハルシネーション（事実誤認）がないか
   - 技術的な正確性

2. 明確性 (Clarity) - 30%
   - 問題文や解説に曖昧さがないか
   - 日本語として自然か
   - 解法が明確に示されているか

3. 教育的価値 (Educational Value) - 30%
   - 単なる丸暗記ではなく、思考を促す良問か
   - セキュリティの理解を深める内容か
   - 適切な難易度設定か

**評価対象:**
```json
{json.dumps(mission_data, indent=2, ensure_ascii=False)}
```

**出力形式:**
以下のJSON形式で評価結果を出力してください:
{{
  "correctness_score": 0-100,
  "clarity_score": 0-100,
  "educational_value_score": 0-100,
  "total_score": 0-100,
  "correctness_feedback": "正確性に関するフィードバック",
  "clarity_feedback": "明確性に関するフィードバック",
  "educational_value_feedback": "教育的価値に関するフィードバック",
  "overall_feedback": "総合的なフィードバック",
  "improvement_suggestions": ["改善提案1", "改善提案2", ...]
}}
"""
        
        try:
            response = self.model.generate_content(
                evaluation_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # 評価は低温度で
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                )
            )
            
            # JSONパース
            json_text = response.text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            feedback = json.loads(json_text)
            score = feedback.get("total_score", 0.0)
            
            return float(score), feedback
            
        except Exception as e:
            print(f"Error evaluating mission: {e}", file=sys.stderr)
            # エラー時はデフォルトスコアを返す
            return 50.0, {
                "error": str(e),
                "total_score": 50.0,
                "overall_feedback": "評価中にエラーが発生しました"
            }
    
    def should_regenerate(self, score: float, threshold: float = 80.0) -> bool:
        """
        再生成が必要かどうかを判定
        
        Args:
            score: 評価スコア
            threshold: 閾値（デフォルト: 80.0）
            
        Returns:
            再生成が必要な場合True
        """
        return score < threshold

