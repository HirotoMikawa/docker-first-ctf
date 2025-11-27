"""
Project Sol: Mission Drafter (Ver 10.2)

Generates draft mission JSON files that pass validation.
Implements Phase 2: Draft Generation (CONTENT_PLAN.md).

Uses OpenAI API (GPT-4o) for AI-powered generation.
"""

import json
import random
import string
import os
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import sys

# Load environment variables
from dotenv import load_dotenv

# OpenAI API
try:
    from openai import OpenAI
except ImportError:
    print("Error: openai library not installed. Run: pip install -r tools/requirements.txt", file=sys.stderr)
    sys.exit(1)

# Load .env file
load_dotenv()

# Add parent directory to path for validator import
sys.path.insert(0, str(Path(__file__).parent.parent))

from ci.validator import MissionValidator


# Allowed types (PROJECT_MASTER.md)
ALLOWED_TYPES = ["RCE", "SQLi", "SSRF", "XXE", "IDOR", "PrivEsc", "LogicError", "Misconfig"]

# Allowed base images (PROJECT_MASTER.md)
ALLOWED_BASE_IMAGES = ["python:3.11-slim", "alpine:3.19"]

# Attack vectors
ATTACK_VECTORS = ["Network", "Local", "Adjacent Network", "Physical"]

# Common tags
COMMON_TAGS = ["web", "linux", "sql", "rce", "xss", "auth", "crypto", "network", "os"]

# Forbidden Words (CONTENT_PLAN.md) - 使用しない
FORBIDDEN_WORDS = [
    "Great", "Good luck", "Happy", "Sorry", "Please", 
    "I think", "Feel", "Hope"
]

# Story hook templates (Forbidden Wordsを含まない)
STORY_HOOK_TEMPLATES = [
    "Target system detected at {ip}. Proceed with investigation.",
    "Unauthorized access detected. Security breach confirmed at {ip}. Immediate action required.",
    "System vulnerability identified. Target located at {ip}. Commence penetration protocol.",
    "Security alert triggered. Target system at {ip} requires immediate assessment.",
    "Intrusion detected. Target at {ip} shows signs of compromise. Proceed with caution.",
    "Network anomaly detected at {ip}. Potential security threat identified.",
    "Target system at {ip} flagged for security review. Investigation protocol initiated.",
    "Security breach confirmed. Target located at {ip}. Execute containment procedures.",
]


class MissionDrafter:
    """Generates draft mission JSON files that pass validation using OpenAI API."""
    
    def __init__(self, output_dir: str = "challenges/drafts", api_key: Optional[str] = None):
        """
        Initialize drafter.
        
        Args:
            output_dir: Directory to save generated drafts
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. "
                "Please set it as an environment variable or pass it as api_key parameter."
            )
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"
    
    def generate_mission_id(self) -> str:
        """Generate mission ID in format SOL-MSN-{4桁の識別子}."""
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"SOL-MSN-{random_suffix}"
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for OpenAI API."""
        return """あなたは、エリートCTFアーキテクト（CTF Architect）であり、フロントエンドデザイナー（Frontend Designer）です。

あなたの任務は、Combat Modeのトーンで、以下のJSON Schemaに100%準拠したCTF問題のシナリオと設定データを作成することです。

**重要な役割:**
- 脆弱なWebアプリケーションを設計・実装する
- 視覚的に没入感があり、ストーリー性のある問題を作成する
- 本物の本番システム（または秘密ツール）のように見える、プロフェッショナルなデザインを実装する
- ユーザーが探索したくなるような「楽しさ」と「情報密度」を提供する

## JSON Schema (必須準拠)

{
  "mission_id": "SOL-MSN-XXX",
  "mission_version": "1.0.0",
  "type": "RCE|SQLi|SSRF|XXE|IDOR|PrivEsc|LogicError|Misconfig",
  "difficulty": 1-5,
  "difficulty_factors": {
    "tech": 1-5,
    "read": 1-5,
    "explore": 1-5
  },
  "vulnerability": {
    "cve_id": "CVE-YYYY-NNNN",
    "cvss": 0.0-10.0,
    "attack_vector": "Network|Local|Adjacent Network|Physical"
  },
  "environment": {
    "image": "sol/mission-xxx:latest",
    "base_image": "python:3.11-slim|alpine:3.19",
    "cost_token": 1000-10000,
    "expected_solve_time": "30m|45m|60m|90m|120m",
    "tags": ["web", "linux", ...]
  },
  "narrative": {
    "story_hook": "最大3文。禁止用語を含まない。",
    "tone": "combat"
  },
  "flag_answer": "SolCTF{...}",
  "files": {
    "app.py": "脆弱なアプリケーションコード（Python/Flask）",
    "Dockerfile": "Dockerfileの内容",
    "requirements.txt": "依存パッケージ（必要な場合）",
    "flag.txt": "SolCTF{...} または flag_answer と同じ値"
  },
  "status": "draft"
}

## 重要な制約

1. **難易度計算式**: difficulty = Clamp(Round(tech * 0.4 + read * 0.2 + explore * 0.4), 1, 5)
   - この計算式に従って、difficultyとdifficulty_factorsを整合させること。

2. **禁止用語 (絶対に使用禁止)**:
   - Words: "Great", "Good luck", "Happy", "Sorry", "Please", "I think", "Feel", "Hope"
   - Punctuation: ! (感嘆符)

3. **story_hook**: 
   - 最大3文
   - Combat Modeのトーン
   - 禁止用語を含まない
   - IPアドレスを含むことが推奨される

4. **mission_id**: "SOL-MSN-" + 4文字の英数字（例: "SOL-MSN-A1B2"）

5. **mission_version**: 常に "1.0.0"

6. **status**: 常に "draft"

7. **tone**: 常に "combat"

8. **flag_answer**: 必須フィールド。`SolCTF{...}` 形式のランダムなフラグ文字列を生成してください。
   - 例: `SolCTF{random_string_123}`, `SolCTF{flag_abc_xyz}`
   - このフラグは、ユーザーが問題を解いた際の正解として使用されます。

9. **files**: 必須フィールド。実際に動作する脆弱なアプリケーションコードを含むオブジェクト。
   - **app.py**: 指定された脆弱性タイプ（例: SQLi, RCE, SSRF等）を含む、最小限のPython/Flaskアプリケーションコード
   - **Dockerfile**: セキュリティ基準（非root実行、ctfuser使用）を守ったDockerfile
   - **requirements.txt**: 必要なPythonパッケージ（Flask等）
   - **flag.txt**: `flag_answer` と同じ値のフラグファイル（オプション）

**セキュリティ基準（PROJECT_MASTER.md準拠）:**
- ユーザー: ctfuser (UID >= 1000) で実行。Root禁止。
- ポート: 8000/tcp のみ公開。
- ベースイメージ: python:3.11-slim または alpine:3.19。
- ネットワーク: 内部ネットワークのみ（外部インターネットアクセス禁止）。

**Dockerfileと依存関係の制約:**
- Pythonライブラリをインストールする際は、**必ずバージョンを固定**すること（互換性エラーを防ぐため）。
- Flaskアプリの場合: `RUN pip install Flask==3.0.0 Werkzeug==3.0.0` を使用すること（`flask` や `Flask` のみの指定は禁止）。
- その他のパッケージも同様に、`package==version` 形式でバージョンを明示すること。
- ベースイメージとの互換性を確保すること（例: python:3.11-slim を使用する場合）。
- **EXPOSE 8000** を必ず含めること。
- **CMD**: `CMD ["python", "app.py"]` または `CMD ["python3", "app.py"]` を使用すること。

**[CRITICAL CONSTRAINTS FOR PYTHON APP]**

1. **ポート設定**: アプリは**必ずポート8000**でリッスンすること。
   - Flaskのデフォルト（ポート5000）は使用禁止。

2. **ホスト設定**: アプリは**必ずホスト '0.0.0.0'** でリッスンすること（外部接続を許可するため）。
   - `localhost` や `127.0.0.1` は使用禁止（Docker環境では接続不可）。

3. **ルートルート**: 必ず `@app.route('/')` を定義し、メインの脆弱性ページにリンクまたはリダイレクトすること。
   - 404エラーを防ぐため、ルートパス '/' は必ず有効なレスポンスを返すこと。

4. **エントリーポイント**: スクリプトの最後に以下を必ず含めること：
   ```python
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=8000)
   ```
   - `app.run()` の引数は `host='0.0.0.0', port=8000` を必ず指定すること。

**[CRITICAL CONSTRAINTS FOR FLASK]**

1. **テンプレート関数**: `render_template()` は**絶対に使用禁止**。代わりに `render_template_string()` を使用すること。
   - `render_template()` は外部HTMLファイルを必要とするため、エラーが発生する。

2. **HTMLの埋め込み**: すべてのHTMLテンプレートをPythonコード内に文字列として直接埋め込むこと。
   - HTMLは `render_template_string()` の引数として文字列リテラルで渡すこと。

3. **外部ファイル禁止**: `templates` フォルダや外部HTMLファイルは作成しないこと。
   - すべてのコードとHTMLは `app.py` 1つのファイルに含めること。

4. **単一ファイル原則**: コードは**SINGLE `app.py` ファイル**で、実行に必要なすべてを含むこと。
   - 外部テンプレートファイル、設定ファイル、静的ファイルは使用しないこと。

**[DESIGN & ATMOSPHERE REQUIREMENTS]**

1. **プロフェッショナルなデザイン**: 生成するアプリには、必ず **Inline CSS (`<style>` タグ)** を含め、プロフェッショナルで没入感のあるデザインにすること。
   - 単純なプレーンテキストやデフォルトスタイルは禁止。
   - 本物の本番システム（または秘密ツール）のように見えること。

2. **テーマ選択**: 以下のテーマから、脆弱性タイプやナラティブに合わせて選択すること：
   - **CORPORATE**: Clean, Bootstrap-like, Blue/White配色、企業ポータル風（"Employee Portal", "Admin Dashboard" スタイル）
   - **UNDERGROUND**: Dark mode、Green text、Terminal font、ハッカー掲示板風（"Hacker Forum", "Dark Web" スタイル）
   - **GOVERNMENT**: Gray/Red配色、"Top Secret" スタンプ、警告バナー、政府機関風（"Classified System" スタイル）

3. **視覚的魅力**: 
   - カラースキーム、フォント、レイアウトを統一し、一貫性のあるデザインにすること。
   - ボタン、フォーム、テーブルなどのUI要素を適切にスタイリングすること。

**[NARRATIVE INTEGRATION REQUIREMENTS]**

1. **ストーリー反映**: 生成された `narrative.story_hook` や `vulnerability` の設定を、HTML内のテキストに反映させること。
   - 例: SQLi問題なら、「Database Error」の表示をリアルにする、あるいは「検索フォーム」に「社員IDを入力してください」などの文言を入れる。
   - 例: RCE問題なら、「システム管理ツール」や「コマンド実行インターフェース」のような文脈を反映する。

2. **コンテキストの一貫性**: 脆弱性タイプ（type）とナラティブが一致するように、適切な文脈を設定すること。
   - 例: SSRF問題なら、「内部ネットワークスキャン」や「プロキシサービス」のような設定にする。

**[INFORMATION DENSITY REQUIREMENTS]**

1. **ダミー情報の追加**: ページがスカスカにならないように、リアルなダミー情報を追加すること。
   - **Fake Footer**: "Copyright 2024 Arasaka Corp." や "All Rights Reserved" などの企業情報
   - **Fake Comments**: HTMLソース内に `<!-- TODO: Remove debug endpoint -->` や `<!-- SECRET: Admin password reset -->` のようなヒント（または引っかけ）を入れる
   - **Fake Menu**: 機能しないダミーボタン（Dashboard, Settings, Logs, Reports等）を配置して「本物のシステムっぽさ」を出す
   - **Fake System Messages**: "System Status: Online", "Last Update: 2024-01-15" などのシステム情報
   - **Fake User Data**: テーブルやリストにダミーのユーザー名、ID、日付などを表示

2. **探索の楽しさ**: ユーザーが探索したくなるような「フレーバーテキスト」を追加すること。
   - システム警告、企業ロゴ（テキスト形式）、フッター情報、隠されたヒントなど。

**コード生成要件:**
- 指定された脆弱性タイプ（type）を含む、実際に動作するアプリケーションコードを作成すること。
- 例: SQLi の場合、SQLインジェクションが可能なログイン画面や検索機能を含む。
- 例: RCE の場合、コマンド実行が可能な脆弱なエンドポイントを含む。
- コードは最小限で、脆弱性を明確に示すものであること。
- フラグは、脆弱性を利用して取得できる場所に配置すること。
- **上記のデザイン要件、ナラティブ統合要件、情報密度要件をすべて満たすこと。**

## 出力形式

JSON形式のみを返してください。説明文やマークダウンは不要です。純粋なJSONオブジェクトのみを返してください。

**重要**: 
- JSONには必ず `"flag_answer": "SolCTF{...}"` を含めること。
- JSONには必ず `"files"` オブジェクトを含め、実際に動作するアプリケーションコードを生成すること。"""
    
    def _build_user_prompt(self, difficulty: Optional[int] = None, mission_type: Optional[str] = None) -> str:
        """Build user prompt for OpenAI API."""
        if difficulty is None:
            difficulty = random.randint(1, 5)
        
        if mission_type is None:
            mission_type = random.choice(ALLOWED_TYPES)
        
        # Difficulty description
        difficulty_descriptions = {
            1: "初心者向け（基本的な情報収集や簡単な脆弱性）",
            2: "初級者向け（基本的なWeb脆弱性やOSコマンド）",
            3: "中級者向け（フィルタ回避が必要な攻撃や権限昇格）",
            4: "上級者向け（複雑な脆弱性チェーンや高度な技術）",
            5: "最上級者向け（複数段階の攻撃や難読化されたコード）"
        }
        
        # Type description
        type_descriptions = {
            "RCE": "Remote Code Execution（リモートコード実行）",
            "SQLi": "SQL Injection（SQLインジェクション）",
            "SSRF": "Server-Side Request Forgery（サーバーサイドリクエスト偽造）",
            "XXE": "XML External Entity（XML外部実体参照）",
            "IDOR": "Insecure Direct Object Reference（不適切な直接オブジェクト参照）",
            "PrivEsc": "Privilege Escalation（権限昇格）",
            "LogicError": "Logic Error（ロジックエラー）",
            "Misconfig": "Misconfiguration（設定ミス）"
        }
        
        prompt = f"""難易度 {difficulty} ({difficulty_descriptions[difficulty]}) の {mission_type} ({type_descriptions[mission_type]}) に関するCTF問題を1つ作成してください。

以下の要件を満たしてください：
- 難易度計算式に従って、difficulty_factorsを正しく設定すること
- story_hookは最大3文で、Combat Modeのトーンを維持すること
- 禁止用語を使用しないこと
- すべての必須フィールドを含めること
- **必ず `flag_answer` フィールドを含め、`SolCTF{{...}}` 形式のランダムなフラグ文字列を生成すること**
- **必ず `files` オブジェクトを含め、指定された脆弱性（{mission_type}）を含む実際に動作するアプリケーションコードを生成すること**
  - `app.py`: {mission_type} 脆弱性を含むPython/Flaskアプリケーション
  - `Dockerfile`: セキュリティ基準（非root実行、ctfuser使用）を守ったDockerfile
  - `requirements.txt`: 必要な依存パッケージ
  - `flag.txt`: flag_answerと同じ値（オプション）
- 生成されるコードは、PROJECT_MASTER.mdのセキュリティ基準（非root実行、ポート8000のみ公開）を守ること
- JSON形式のみで返答すること"""
        
        return prompt
    
    def _generate_with_ai(self, difficulty: Optional[int] = None, mission_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate mission JSON using OpenAI API.
        
        Args:
            difficulty: Target difficulty (1-5). If None, random.
            mission_type: Target mission type. If None, random.
            
        Returns:
            Mission JSON dictionary
            
        Raises:
            Exception: If API call fails
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(difficulty, mission_type)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse JSON response
            content = response.choices[0].message.content
            mission = json.loads(content)
            
            # Ensure mission_id is set (generate if missing)
            if "mission_id" not in mission or not mission["mission_id"]:
                mission["mission_id"] = self.generate_mission_id()
            
            # Ensure required fields
            if "mission_version" not in mission:
                mission["mission_version"] = "1.0.0"
            if "status" not in mission:
                mission["status"] = "draft"
            if "narrative" not in mission:
                mission["narrative"] = {}
            if "tone" not in mission.get("narrative", {}):
                mission["narrative"]["tone"] = "combat"
            
            # Ensure flag_answer is present (generate if missing)
            if "flag_answer" not in mission or not mission.get("flag_answer"):
                # Generate a random flag in SolCTF{...} format
                random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
                mission["flag_answer"] = f"SolCTF{{{random_suffix}}}"
            
            # Ensure files object is present (generate fallback if missing)
            if "files" not in mission or not mission.get("files"):
                # Fallback: Generate minimal files if AI didn't generate them
                flag_value = mission.get("flag_answer", "SolCTF{default_flag}")
                base_image = mission.get("environment", {}).get("base_image", "python:3.11-slim")
                is_alpine = "alpine" in base_image.lower()
                
                # Generate minimal Dockerfile (with version-pinned dependencies)
                if is_alpine:
                    dockerfile_content = f"""FROM {base_image}
RUN apk add --no-cache python3 py3-pip && \\
    adduser -D -u 1000 ctfuser
COPY app.py requirements.txt /home/ctfuser/
RUN pip3 install --no-cache-dir -r /home/ctfuser/requirements.txt
USER ctfuser
WORKDIR /home/ctfuser
EXPOSE 8000
ENV CTF_FLAG={flag_value}
CMD ["python3", "app.py"]
"""
                else:
                    dockerfile_content = f"""FROM {base_image}
RUN useradd -m -u 1000 ctfuser
COPY app.py requirements.txt /home/ctfuser/
RUN pip3 install --no-cache-dir -r /home/ctfuser/requirements.txt
USER ctfuser
WORKDIR /home/ctfuser
EXPOSE 8000
ENV CTF_FLAG={flag_value}
CMD ["python3", "app.py"]
"""
                
                # Generate minimal app.py (placeholder) - with correct host/port settings
                app_py_content = f"""from flask import Flask, request, render_template_string
import os

app = Flask(__name__)
FLAG = os.getenv('CTF_FLAG', '{flag_value}')

@app.route('/')
def index():
    return '<html><body style="background-color:black; color:lime; display:flex; justify-content:center; align-items:center; height:100vh; font-family:monospace;"><h1>Mission Started: Target System Online</h1></body></html>'

if __name__ == '__main__':
    # CRITICAL: Must use host='0.0.0.0' and port=8000 for Docker environment
    app.run(host='0.0.0.0', port=8000)
"""
                
                mission["files"] = {
                    "app.py": app_py_content,
                    "Dockerfile": dockerfile_content,
                    "requirements.txt": "Flask==3.0.0\nWerkzeug==3.0.0",
                    "flag.txt": flag_value
                }
            
            return mission
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response from OpenAI: {e}")
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")
    
    def generate_difficulty_factors(self, target_difficulty: int) -> Dict[str, int]:
        """
        Generate difficulty factors that match the target difficulty.
        
        Formula: Difficulty = Clamp(Round(Tech * 0.4 + Read * 0.2 + Explore * 0.4), 1, 5)
        
        Args:
            target_difficulty: Target difficulty (1-5)
            
        Returns:
            Dictionary with tech, read, explore factors
        """
        # Try different combinations until we find one that matches
        max_attempts = 100
        for _ in range(max_attempts):
            # Generate factors based on target difficulty
            if target_difficulty == 1:
                tech = random.randint(1, 2)
                read = random.randint(1, 2)
                explore = random.randint(1, 2)
            elif target_difficulty == 2:
                tech = random.randint(2, 3)
                read = random.randint(2, 3)
                explore = random.randint(2, 3)
            elif target_difficulty == 3:
                tech = random.randint(3, 4)
                read = random.randint(3, 4)
                explore = random.randint(3, 4)
            elif target_difficulty == 4:
                tech = 4
                read = random.randint(3, 4)
                explore = 4
            else:  # difficulty == 5
                tech = random.randint(4, 5)
                read = random.randint(3, 5)
                explore = random.randint(4, 5)
            
            # Calculate resulting difficulty
            calculated = round(tech * 0.4 + read * 0.2 + explore * 0.4)
            calculated = max(1, min(5, calculated))
            
            if calculated == target_difficulty:
                return {
                    "tech": tech,
                    "read": read,
                    "explore": explore
                }
        
        # Fallback: use values that should work
        if target_difficulty == 1:
            return {"tech": 1, "read": 1, "explore": 1}
        elif target_difficulty == 2:
            return {"tech": 2, "read": 2, "explore": 2}
        elif target_difficulty == 3:
            return {"tech": 3, "read": 3, "explore": 3}
        elif target_difficulty == 4:
            return {"tech": 4, "read": 4, "explore": 4}
        else:
            return {"tech": 5, "read": 4, "explore": 5}
    
    def generate_ip_address(self) -> str:
        """Generate a random IP address for story hook."""
        return f"{random.randint(192, 223)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    def generate_story_hook(self) -> str:
        """
        Generate story hook (max 3 sentences, no forbidden words).
        
        Returns:
            Story hook text
        """
        ip = self.generate_ip_address()
        template = random.choice(STORY_HOOK_TEMPLATES)
        story_hook = template.format(ip=ip)
        
        # Ensure it's max 3 sentences
        # Split by sentence endings, but be careful with IP addresses
        # Replace IP address temporarily to avoid splitting on it
        import re
        ip_placeholder = "___IP_ADDRESS___"
        story_hook_safe = story_hook.replace(ip, ip_placeholder)
        
        # Split by sentence endings (period, exclamation, question mark)
        # But not if they're part of an IP address
        sentences = re.split(r'[.!?]+\s+', story_hook_safe)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Restore IP address
        sentences = [s.replace(ip_placeholder, ip) for s in sentences]
        
        # Ensure max 3 sentences
        if len(sentences) > 3:
            story_hook = '. '.join(sentences[:3]) + '.'
        elif len(sentences) == 0:
            # Fallback if something went wrong
            story_hook = f"Target system detected at {ip}. Proceed with investigation."
        else:
            # Join sentences back
            story_hook = '. '.join(sentences)
            if not story_hook.endswith(('.', '!', '?')):
                story_hook += '.'
        
        return story_hook
    
    def generate_cve_id(self) -> str:
        """Generate a CVE ID in format CVE-YYYY-NNNN."""
        year = random.randint(2020, 2024)
        number = random.randint(1, 9999)
        return f"CVE-{year}-{number:04d}"
    
    def generate_mission(self, difficulty: int = None) -> Dict[str, Any]:
        """
        Generate a complete mission JSON.
        
        Args:
            difficulty: Target difficulty (1-5). If None, random.
            
        Returns:
            Mission JSON dictionary
        """
        if difficulty is None:
            difficulty = random.randint(1, 5)
        
        mission_type = random.choice(ALLOWED_TYPES)
        mission_id = self.generate_mission_id()
        difficulty_factors = self.generate_difficulty_factors(difficulty)
        
        # Generate CVE ID and CVSS
        cve_id = self.generate_cve_id()
        cvss = round(random.uniform(5.0, 9.5), 1)
        
        # Generate environment
        base_image = random.choice(ALLOWED_BASE_IMAGES)
        image_name = f"sol/mission-{mission_id.lower().replace('-', '_')}:latest"
        cost_token = random.randint(1000, 10000)
        solve_time_minutes = random.choice([30, 45, 60, 90, 120])
        expected_solve_time = f"{solve_time_minutes}m"
        
        # Generate tags (2-4 tags)
        num_tags = random.randint(2, 4)
        tags = random.sample(COMMON_TAGS, min(num_tags, len(COMMON_TAGS)))
        
        # Generate story hook
        story_hook = self.generate_story_hook()
        
        mission = {
            "mission_id": mission_id,
            "mission_version": "1.0.0",
            "type": mission_type,
            "difficulty": difficulty,
            "difficulty_factors": difficulty_factors,
            "vulnerability": {
                "cve_id": cve_id,
                "cvss": cvss,
                "attack_vector": random.choice(ATTACK_VECTORS)
            },
            "environment": {
                "image": image_name,
                "base_image": base_image,
                "cost_token": cost_token,
                "expected_solve_time": expected_solve_time,
                "tags": tags
            },
            "narrative": {
                "story_hook": story_hook,
                "tone": "combat"
            },
            "status": "draft"
        }
        
        return mission
    
    def draft(self, difficulty: int = None, max_retries: int = 3, verbose: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Generate and validate a mission draft using OpenAI API.
        
        Args:
            difficulty: Target difficulty (1-5). If None, random.
            max_retries: Maximum retry attempts if validation fails (default: 3)
            verbose: Print validation errors for debugging
            
        Returns:
            Tuple of (success, file_path, mission_data)
        """
        for attempt in range(max_retries):
            try:
                # Generate mission using AI
                mission = self._generate_with_ai(difficulty)
                
                # Validate
                validator = MissionValidator(mission)
                is_valid, errors, warnings = validator.validate_all()
                
                if is_valid:
                    # Save to file
                    mission_id = mission["mission_id"]
                    file_path = self.output_dir / f"{mission_id}.json"
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(mission, f, indent=2, ensure_ascii=False)
                    
                    return True, str(file_path), mission
                else:
                    # Retry if validation failed
                    if verbose:
                        print(f"Attempt {attempt + 1}/{max_retries} failed validation:", file=sys.stderr)
                        for error in errors:
                            print(f"  ✗ {error}", file=sys.stderr)
                    continue
                    
            except ValueError as e:
                # JSON parse error
                if verbose:
                    print(f"Attempt {attempt + 1}/{max_retries} failed (JSON parse error): {e}", file=sys.stderr)
                continue
            except RuntimeError as e:
                # API error
                error_msg = str(e)
                if "API key" in error_msg.lower() or "authentication" in error_msg.lower():
                    raise RuntimeError(
                        "OpenAI API authentication failed. "
                        "Please check your OPENAI_API_KEY environment variable."
                    )
                elif "rate limit" in error_msg.lower():
                    raise RuntimeError(
                        "OpenAI API rate limit exceeded. "
                        "Please wait a moment and try again."
                    )
                else:
                    if verbose:
                        print(f"Attempt {attempt + 1}/{max_retries} failed (API error): {e}", file=sys.stderr)
                    if attempt == max_retries - 1:
                        # Last attempt, raise the error
                        raise
                    continue
            except Exception as e:
                # Unexpected error
                if verbose:
                    print(f"Attempt {attempt + 1}/{max_retries} failed (unexpected error): {e}", file=sys.stderr)
                if attempt == max_retries - 1:
                    raise
                continue
        
        # Failed to generate valid mission after max_retries
        return False, "", {}


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate draft mission JSON using OpenAI API")
    parser.add_argument(
        '--difficulty',
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=None,
        help='Target difficulty (1-5). If not specified, random.'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='challenges/drafts',
        help='Output directory for drafts'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='OpenAI API key (if not set, reads from OPENAI_API_KEY env var)'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts if validation fails (default: 3)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed error messages'
    )
    
    args = parser.parse_args()
    
    try:
        drafter = MissionDrafter(output_dir=args.output_dir, api_key=args.api_key)
        success, file_path, mission = drafter.draft(
            difficulty=args.difficulty,
            max_retries=args.max_retries,
            verbose=args.verbose
        )
        
        if success:
            print(f"✓ Draft generated successfully: {file_path}")
            print(f"  Mission ID: {mission['mission_id']}")
            print(f"  Type: {mission['type']}")
            print(f"  Difficulty: {mission['difficulty']}")
            return 0
        else:
            print("✗ Failed to generate valid draft after multiple attempts", file=sys.stderr)
            return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

