"""
Project Sol: Gemini-based Mission Drafter (Ver 11.0)

HyRAG-QG architecture implementation using Gemini 1.5 Flash API.
Replaces OpenAI GPT-4o with Gemini for cost-effective generation.
"""

import json
import random
import string
import os
import asyncio
import time
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path
import sys

# Load environment variables
from dotenv import load_dotenv

# Google Gemini API
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    print("Error: google-generativeai library not installed. Run: pip install google-generativeai", file=sys.stderr)
    sys.exit(1)

# LangChain for orchestration
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    print("Warning: langchain libraries not installed. RAG features will be limited.", file=sys.stderr)

# BudouX for Japanese text processing
try:
    import budoux
    HAS_BUDOUX = True
except ImportError:
    HAS_BUDOUX = False
    print("Warning: budoux library not installed. Japanese text processing will be limited.", file=sys.stderr)

# Tenacity for retry logic
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type
    )
    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False
    print("Warning: tenacity library not installed. Retry logic will be limited.", file=sys.stderr)

# Load .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ci.validator import MissionValidator
from generation.models import CTFMission

# Rate limiter for Gemini API (15 RPM)
_last_request_time = 0
_min_request_interval = 4.0  # 60 seconds / 15 requests = 4 seconds per request


def _rate_limit():
    """Rate limiter for Gemini API (15 RPM)"""
    global _last_request_time
    current_time = time.time()
    elapsed = current_time - _last_request_time
    if elapsed < _min_request_interval:
        time.sleep(_min_request_interval - elapsed)
    _last_request_time = time.time()


class GeminiMissionDrafter:
    """
    CTF問題生成器（Gemini API版）
    
    HyRAG-QGアーキテクチャに基づく実装:
    - Gemini 1.5 Flash API（無料枠）を使用
    - Pydanticによる構造化出力
    - LangChainによるオーケストレーション
    - ChromaDBによるベクトルストア（オプション）
    """
    
    def __init__(self, output_dir: str = "challenges/drafts", api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            output_dir: 出力ディレクトリ
            api_key: Gemini APIキー（Noneの場合は環境変数から読み込み）
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Gemini API設定
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable or api_key parameter is required")
        
        genai.configure(api_key=api_key)
        
        # Gemini 2.0 Flashモデル（設計書では1.5 Flashと記載されているが、実際には2.0 Flashが利用可能）
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # BudouX初期化
        if HAS_BUDOUX:
            try:
                # BudouX 0.7.0以降はload_default_japanese_parser()を使用
                self.budoux_parser = budoux.load_default_japanese_parser()
            except (AttributeError, TypeError):
                # フォールバック: 古いバージョンまたはエラー時
                self.budoux_parser = None
        else:
            self.budoux_parser = None
        
        # Validator (初期化時は不要、使用時にmission_dataを渡す)
        # self.validator は使用時に MissionValidator(mission_data) として作成
    
    def _build_system_prompt(self, category: str = None, theme: str = None, source_text: str = None) -> str:
        """
        システムプロンプトを構築
        
        Args:
            category: カテゴリ（オプション）
            theme: テーマ（オプション）
            source_text: 外部テキスト（RAG用、オプション）
        """
        base_prompt = """あなたは、エリートCTFアーキテクト（CTF Architect）であり、フロントエンドデザイナー（Frontend Designer）です。

あなたの任務は、Combat Modeのトーンで、以下のJSON Schemaに100%準拠したCTF問題のシナリオと設定データを作成することです。

**重要な役割:**
- 脆弱なWebアプリケーションを設計・実装する
- 視覚的に没入感があり、ストーリー性のある問題を作成する
- 本物の本番システム（または秘密ツール）のように見える、プロフェッショナルなデザインを実装する
- ユーザーが探索したくなるような「楽しさ」と「情報密度」を提供する

**言語要件（必須）:**
- **問題のタイトル、説明、ストーリーフック、解説（writeup）はすべて日本語で記述してください**
- 英語の専門用語（例: SQL Injection, XSS, RCE）は使用可能ですが、説明は日本語で行ってください
- writeupは初心者でも理解できるよう、詳細なステップバイステップの日本語解説を含めてください
- コマンド例やURL例には、実際に使用するポート番号のプレースホルダー（{{CONTAINER_HOST}}）を含めてください

**出力形式:**
Pydanticモデル（CTFMission）に完全に準拠したJSON形式で出力してください。
すべてのフィールドが必須であり、型とバリデーションルールを厳密に守ってください。

**禁止用語 (絶対に使用禁止):**
- Words: "Great", "Good luck", "Happy", "Sorry", "Please", "I think", "Feel", "Hope"
- Punctuation: ! (感嘆符)

**セキュリティ基準:**
- ユーザー: ctfuser (UID >= 1000) で実行。Root禁止。
- ポート: 8000/tcp のみ公開。
- ベースイメージ: python:3.11-slim または alpine:3.19。
- ネットワーク: 内部ネットワークのみ（外部インターネットアクセス禁止）。

**Dockerfile制約:**
- python:3.11-slimの場合: `RUN useradd -m -u 1000 ctfuser`（-s /bin/bashなし）
- alpine:3.19の場合: `RUN adduser -D -u 1000 ctfuser`
- **フラグ配置は問題タイプに応じて（CRITICAL - 必ず守ること）:**
  - **RCE/LFI/PrivEsc/Misconfig** → **必ず** `/home/ctfuser/flag.txt` に配置
    - 例: `RUN echo "SolCTF{...}" > /home/ctfuser/flag.txt && chmod 644 /home/ctfuser/flag.txt`
    - **絶対に** `/flag.txt` に配置しないこと
  - **SQLi/XSS/SSRF/XXE/IDOR** → `/flag.txt` + `ENV FLAG="SolCTF{...}"`
    - 例: `RUN echo "SolCTF{...}" > /flag.txt && chmod 644 /flag.txt`
    - 例: `ENV FLAG="SolCTF{...}"`
  - **LogicError/Crypto** → 柔軟
- **パッケージ名の注意**: Debian/Ubuntuでは正しいパッケージ名を使用すること
  - ❌ `iputils` (存在しない) → ✅ `iputils-ping` または `iputils-tracepath`
  - ❌ `netcat` → ✅ `netcat-traditional` または `netcat-openbsd`
  - パッケージが存在するか確認してから使用すること

**Flaskアプリ制約:**
- ポート8000、ホスト0.0.0.0でリッスン
- ルートルート '/' を必ず定義
- render_template_stringは文字列フォーマット（.format()）を使用
- SQLi問題はデータベース初期化（init_db()）を含める

**[CRITICAL: 品質管理ルール - デバッグエンドポイントと脆弱性実装]**

⚠️ 以下は絶対に守ること ⚠️

**1. デバッグエンドポイントの禁止:**
- ❌ `@app.route('/flag')` でフラグを直接返す
- ❌ `@app.route('/debug')` でデバッグ情報を返す
- ❌ `@app.route('/admin')` で管理画面を露出
- **理由**: 脆弱性を突かずに簡単に解けてしまう

**2. 脆弱性が実際に動作する実装:**

**RCE/Command Injection問題の場合:**
- ✅ `subprocess.run(cmd, shell=True, ...)` を使用
- ❌ `subprocess.run(['echo', cmd], shell=False, ...)` は使用禁止
- ✅ 出力をユーザーに返す（`capture_output=False` または結果を表示）
- ❌ `capture_output=True` で出力を隠さない

**SQLi問題の場合:**
- ✅ 文字列連結: `f"SELECT * FROM users WHERE id='{user_input}'"`
- ❌ Prepared statement: `cursor.execute("SELECT * FROM users WHERE id=?", (user_input,))` は使用禁止

**3. コメントと実装の整合性:**
- コメントで「脆弱性がある」と書いたら、実装も脆弱にする
- セキュアな実装をしてはいけない（問題として成立しない）

**[CRITICAL: 品質管理ルール - デバッグエンドポイント禁止]**

⚠️ 以下のようなデバッグ用エンドポイントは **絶対に作成しないでください** ⚠️

**禁止事項:**
1. **フラグを直接返すエンドポイント**
   - ❌ `@app.route('/flag')` - フラグを直接読み取って返す
   - ❌ `@app.route('/debug')` - デバッグ情報を返す
   - ❌ `@app.route('/admin')` - 管理画面でフラグを表示
   - **理由**: 脆弱性を突かずに簡単に解けてしまう

2. **セキュアな設定の使用禁止（脆弱性問題の場合）**
   - ❌ `subprocess.run(..., shell=False)` - コマンドインジェクション問題では `shell=True` を使用すること
   - ❌ `subprocess.run(..., capture_output=True)` - 出力をユーザーに見せる必要がある場合は使用しない
   - ❌ `prepared statements` - SQLインジェクション問題では文字列連結を使用すること
   - **理由**: 脆弱性が動作しなくなる

3. **意図しない情報漏洩**
   - ❌ エラーメッセージにフラグやパスを含める
   - ❌ HTMLコメントにヒントを含める（探索要素として意図的な場合を除く）
   - ❌ ソースコード内に直接フラグを埋め込む（ファイルから読み取るべき）

**正しい実装例（RCE問題）:**
```python
# ✅ 正しい: shell=True で脆弱性が動作する
@app.route('/', methods=['POST'])
def execute():
    cmd = request.form['cmd']
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

# ❌ 間違い: shell=False で脆弱性が防がれる
@app.route('/', methods=['POST'])
def execute():
    cmd = request.form['cmd']
    result = subprocess.run(['echo', cmd], shell=False, capture_output=True, text=True)
    return result.stdout
```

**正しい実装例（SQLi問題）:**
```python
# ✅ 正しい: 文字列連結で脆弱性が動作する
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    return result

# ❌ 間違い: Prepared statementで脆弱性が防がれる
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    query = "SELECT * FROM users WHERE username=? AND password=?"
    result = db.execute(query, (username, password))
    return result
```

**フラグの取得方法:**
- ✅ 脆弱性を突いてコマンド実行 → `cat /home/ctfuser/flag.txt`
- ✅ SQLインジェクションでデータベース読み取り → `SELECT flag FROM flags`
- ❌ `/flag` エンドポイントに直接アクセス

**Dockerfile構文の注意:**
- COPYコマンドで複数ファイルをコピーする場合、宛先はディレクトリで末尾に`/`が必要
  - ❌ `COPY app.py requirements.txt .` (エラー)
  - ✅ `COPY app.py requirements.txt ./` (正しい)
  - ✅ `COPY app.py requirements.txt /app/` (正しい)
- 単一ファイルの場合は末尾の`/`は不要
  - ✅ `COPY app.py .` (正しい)
  - ✅ `COPY app.py /app/` (正しい)
- **WORKDIRとCOPYの順序（CRITICAL）:**
  - ❌ `COPY app.py ./` → `WORKDIR /home/ctfuser` → `CMD ["python", "app.py"]` (エラー: app.pyが見つからない)
  - ✅ `WORKDIR /home/ctfuser` → `COPY app.py ./` → `CMD ["python", "app.py"]` (正しい)
  - または: `COPY app.py /home/ctfuser/` → `WORKDIR /home/ctfuser` → `CMD ["python", "app.py"]` (正しい)
  - **重要**: COPYの前にWORKDIRを設定するか、COPYの宛先を絶対パスで指定すること

**[CRITICAL: FILE PERSISTENCE RULE - HIGHEST PRIORITY]**

⚠️ THIS IS THE MOST CRITICAL RULE. YOU MUST FOLLOW IT EXACTLY. ⚠️

**If your challenge scenario involves reading a file (e.g., "/flag.txt", "/app/config.php", "/home/ctfuser/flag.txt", "database.db"), you MUST ensure this file is created in the Dockerfile.**

**Requirement:**

1. **File Creation in Dockerfile**: In the `Dockerfile` content you generate, use `RUN` commands to create ALL files that are referenced in `app.py`.
   - **BAD**: Assuming the file exists without creating it.
   - **GOOD**: `RUN echo "SolCTF{...}" > /flag.txt && chmod 644 /flag.txt`
   - **GOOD**: `RUN sqlite3 database.db "CREATE TABLE users (...)"` (if database.db is referenced)

2. **Path Consistency**: The path in `app.py` (e.g., `open("/flag.txt")`, `cat /flag.txt`) MUST match the path in `Dockerfile` (e.g., `RUN echo ... > /flag.txt`).
   - If `app.py` reads `/flag.txt`, then Dockerfile MUST create `/flag.txt`.
   - If `app.py` reads `/home/ctfuser/flag.txt`, then Dockerfile MUST create `/home/ctfuser/flag.txt`.
   - If `app.py` reads `database.db`, then Dockerfile MUST create `database.db` with proper initialization.

3. **Permissions**: Ensure the `ctfuser` can read/write the files as needed.
   - Use `chmod 644` for read-only files.
   - Use `chown ctfuser:ctfuser` if needed (before `USER ctfuser`).

4. **Execution Order**: File creation MUST happen BEFORE `USER ctfuser` (as root).
   - Correct order: 1) FROM, 2) RUN useradd/adduser, 3) **RUN echo ... > file.txt (create files)**, 4) COPY files, 5) RUN pip install, 6) USER ctfuser, 7) WORKDIR, 8) EXPOSE, 9) CMD

5. **Database Files**: If `app.py` uses SQLite (`database.db`), you MUST initialize it in Dockerfile:
   ```dockerfile
   RUN sqlite3 /home/ctfuser/database.db "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT); INSERT INTO users VALUES (1, 'admin', 'password123');"
   RUN chown ctfuser:ctfuser /home/ctfuser/database.db
   ```

6. **The `files` JSON object MUST include "app.py", "Dockerfile", and any other required files.**

7. **DO NOT assume files exist. CREATE THEM in the Dockerfile.**

**VERIFICATION CHECKLIST:**
Before submitting your Dockerfile, verify:
- [ ] Every file referenced in `app.py` (via `open()`, `cat`, `sqlite3`, etc.) is created in Dockerfile
- [ ] File paths in `app.py` match file paths in Dockerfile exactly
- [ ] File creation happens BEFORE `USER ctfuser`
- [ ] File permissions allow `ctfuser` to read/write as needed
- [ ] Database files (if any) are initialized with proper schema and data
"""
        
        # source_textがある場合の追加指示
        if source_text:
            base_prompt += f"""

**[RAG MODE: SOURCE TEXT PROVIDED]**

Create a CTF challenge based strictly on the provided technical description below.

**Source Text:**
{source_text}

**Instructions:**
- Analyze the source text and identify the vulnerability type described.
- Generate a CTF challenge that demonstrates this exact vulnerability.
- Ensure the challenge code accurately reflects the vulnerability described in the source text.
- The challenge should be educational and allow players to exploit the vulnerability as described.
"""
        
        return base_prompt
    
    def _build_user_prompt(self, difficulty: Optional[int] = None, mission_type: Optional[str] = None, source_text: str = None) -> str:
        """
        ユーザープロンプトを構築
        
        Args:
            difficulty: 難易度（1-5）
            mission_type: 問題タイプ（RCE/SQLi等）
            source_text: 外部テキスト（RAG用、オプション）
        """
        mission_id = f"SOL-MSN-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        
        if source_text:
            # RAGモード: source_textに基づいて生成
            prompt = f"""以下のCTF問題を生成してください。

**ミッションID**: {mission_id}
**難易度**: {difficulty if difficulty else "ランダム（1-5）"}
**問題タイプ**: {mission_type if mission_type else "ソーステキストから推測"}

**要件:**
1. 提供されたソーステキストの内容に基づいて、その脆弱性を正確に再現するCTF問題を作成してください
2. **すべてのテキスト（タイトル、説明、ストーリーフック、解説）は日本語で記述してください**
3. すべてのフィールドを完全に埋めてください
4. 難易度計算式に従ってください: difficulty = Clamp(Round(tech * 0.4 + read * 0.2 + explore * 0.4), 1, 5)
5. story_hookは最大3文、Combat Modeのトーン、禁止用語なし、日本語で記述
6. flag_answerはSolCTF{{...}}形式のランダムな文字列
7. 実際に動作する脆弱なアプリケーションコードを生成してください
8. Dockerfileはセキュリティ基準を守り、app.pyで参照するすべてのファイルを作成してください
9. 解説（writeup）は日本語で記述し、探索ベースの詳細な解法を含めてください。ポート番号は{{CONTAINER_HOST}}プレースホルダーを使用してください（例: http://{{CONTAINER_HOST}}/path）

**出力形式（必須）:**
以下のJSONスキーマに完全に準拠してください。すべてのフィールドが必須です。

{{
  "mission_id": "SOL-MSN-XXXX",
  "mission_version": "1.0.0",
  "type": "RCE",
  "difficulty": 3,
  "difficulty_factors": {{
    "tech": 3,
    "read": 2,
    "explore": 4
  }},
  "vulnerability": {{
    "cve_id": "CVE-2024-1234",
    "cvss": 7.5,
    "attack_vector": "Network"
  }},
  "environment": {{
    "image": "sol/mission-xxxx:latest",
    "base_image": "python:3.11-slim",
    "cost_token": 5000,
    "expected_solve_time": "60m",
    "tags": ["web", "rce"]
  }},
  "narrative": {{
    "story_hook": "ストーリーフック（最大3文）",
    "tone": "combat"
  }},
  "flag_answer": "SolCTF{{example_flag}}",
  "files": {{
    "app.py": "完全なPythonコード",
    "Dockerfile": "完全なDockerfile",
    "requirements.txt": "Flask==3.0.0\\nWerkzeug==3.0.0",
    "flag.txt": "SolCTF{{example_flag}}"
  }},
  "writeup": "# 解説\\n\\n## 概要\\n\\nこの問題は...（日本語で詳細に記述）\\n\\n## 解法手順\\n\\n1. まず、http://{{CONTAINER_HOST}}/ にアクセスします\\n2. ...（実際のポート番号は{{CONTAINER_HOST}}を使用）\\n\\n## 学んだこと\\n\\n...",
  "tags": ["Web", "RCE", "Beginner"],
  "status": "draft"
}}

**重要:**
- すべてのフィールドを必ず含めてください
- filesオブジェクトのキーは "app.py", "Dockerfile", "requirements.txt", "flag.txt" を使用してください
- **flag.txtの内容はflag_answerと同じ値にしてください**（例: flag_answerが"SolCTF{{abc}}"なら、flag.txtも"SolCTF{{abc}}"）
- type, difficulty_factors, vulnerability, environment, narrative, flag_answer, files, writeup, tags はすべて必須です
"""
        else:
            # 通常モード
            prompt = f"""以下のCTF問題を生成してください。

**ミッションID**: {mission_id}
**難易度**: {difficulty if difficulty else "ランダム（1-5）"}
**問題タイプ**: {mission_type if mission_type else "ランダム（RCE/SQLi/SSRF/XXE/IDOR/PrivEsc/LogicError/Misconfig）"}

**要件:**
1. **すべてのテキスト（タイトル、説明、ストーリーフック、解説）は日本語で記述してください**
2. すべてのフィールドを完全に埋めてください
3. 難易度計算式に従ってください: difficulty = Clamp(Round(tech * 0.4 + read * 0.2 + explore * 0.4), 1, 5)
4. story_hookは最大3文、Combat Modeのトーン、禁止用語なし、日本語で記述
5. flag_answerはSolCTF{{...}}形式のランダムな文字列
6. 実際に動作する脆弱なアプリケーションコードを生成してください
7. Dockerfileはセキュリティ基準を守り、app.pyで参照するすべてのファイルを作成してください
8. 解説（writeup）は日本語で記述し、探索ベースの詳細な解法を含めてください。ポート番号は{{CONTAINER_HOST}}プレースホルダーを使用してください（例: http://{{CONTAINER_HOST}}/path）

**出力形式（必須）:**
以下のJSONスキーマに完全に準拠してください。すべてのフィールドが必須です。

{{
  "mission_id": "SOL-MSN-XXXX",
  "mission_version": "1.0.0",
  "type": "RCE",
  "difficulty": 3,
  "difficulty_factors": {{
    "tech": 3,
    "read": 2,
    "explore": 4
  }},
  "vulnerability": {{
    "cve_id": "CVE-2024-1234",
    "cvss": 7.5,
    "attack_vector": "Network"
  }},
  "environment": {{
    "image": "sol/mission-xxxx:latest",
    "base_image": "python:3.11-slim",
    "cost_token": 5000,
    "expected_solve_time": "60m",
    "tags": ["web", "rce"]
  }},
  "narrative": {{
    "story_hook": "ストーリーフック（最大3文）",
    "tone": "combat"
  }},
  "flag_answer": "SolCTF{{example_flag}}",
  "files": {{
    "app.py": "完全なPythonコード",
    "Dockerfile": "完全なDockerfile",
    "requirements.txt": "Flask==3.0.0\\nWerkzeug==3.0.0",
    "flag.txt": "SolCTF{{example_flag}}"
  }},
  "writeup": "# 解説\\n\\n## 概要\\n\\nこの問題は...（日本語で詳細に記述）\\n\\n## 解法手順\\n\\n1. まず、http://{{CONTAINER_HOST}}/ にアクセスします\\n2. ...（実際のポート番号は{{CONTAINER_HOST}}を使用）\\n\\n## 学んだこと\\n\\n...",
  "tags": ["Web", "RCE", "Beginner"],
  "status": "draft"
}}

**重要:**
- すべてのフィールドを必ず含めてください
- filesオブジェクトのキーは "app.py", "Dockerfile", "requirements.txt", "flag.txt" を使用してください
- **flag.txtの内容はflag_answerと同じ値にしてください**（例: flag_answerが"SolCTF{{abc}}"なら、flag.txtも"SolCTF{{abc}}"）
- type, difficulty_factors, vulnerability, environment, narrative, flag_answer, files, writeup, tags はすべて必須です
"""
        return prompt
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    ) if HAS_TENACITY else lambda x: x
    def _generate_with_gemini(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Gemini APIを使用して問題を生成
        
        Args:
            system_prompt: システムプロンプト
            user_prompt: ユーザープロンプト
            
        Returns:
            生成されたJSONデータ
        """
        _rate_limit()
        
        # プロンプトを結合
        full_prompt = f"""{system_prompt}

{user_prompt}

**重要**: CTFMissionモデルに完全に準拠したJSON形式で出力してください。
"""
        
        try:
            # Gemini API呼び出し（構造化出力）
            # Note: Gemini APIの構造化出力はPydanticモデルを直接サポートしていないため、
            # JSON形式で出力を要求し、後でPydanticで検証する
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                )
            )
            
            # JSONパース
            json_text = response.text.strip()
            # JSONコードブロックを除去
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            data = json.loads(json_text)
            
            # ファイル構造を変換（Gemini APIが返すキー名をPydanticモデルの期待する形式に変換）
            if "files" in data:
                files_data = data["files"]
                # Gemini APIが app_py や dockerfile を返す場合、app.py と Dockerfile に変換
                # または、そのまま app.py と Dockerfile が返される場合もある
                if "app_py" in files_data and "app.py" not in files_data:
                    files_data["app.py"] = files_data.pop("app_py")
                if "dockerfile" in files_data and "Dockerfile" not in files_data:
                    files_data["Dockerfile"] = files_data.pop("dockerfile")
                if "requirements_txt" in files_data and "requirements.txt" not in files_data:
                    files_data["requirements.txt"] = files_data.pop("requirements_txt")
                if "flag_txt" in files_data and "flag.txt" not in files_data:
                    files_data["flag.txt"] = files_data.pop("flag_txt")
            
            # Gemini APIがリスト形式で返す場合があるため、チェック
            if isinstance(data, list):
                if len(data) == 0:
                    raise ValueError("Gemini API returned an empty list")
                data = data[0]  # 最初の要素を取得
            
            # Pydanticモデルで検証（populate_by_name=Trueにより、app.pyとapp_pyの両方を受け入れる）
            mission = CTFMission(**data)
            # 出力時はaliasを使用
            result = mission.model_dump(by_alias=True)
            # ファイル名を元に戻す
            if "files" in result:
                files_result = result["files"]
                if "app_py" in files_result:
                    files_result["app.py"] = files_result.pop("app_py")
                if "dockerfile" in files_result:
                    files_result["Dockerfile"] = files_result.pop("dockerfile")
                if "requirements_txt" in files_result:
                    files_result["requirements.txt"] = files_result.pop("requirements_txt")
                if "flag_txt" in files_result:
                    files_result["flag.txt"] = files_result.pop("flag_txt")
            return result
            
        except Exception as e:
            print(f"Error generating with Gemini: {e}", file=sys.stderr)
            raise
    
    def draft(self, difficulty: Optional[int] = None, mission_type: Optional[str] = None,
              max_retries: int = 3, verbose: bool = False, source_text: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        問題を生成
        
        Args:
            difficulty: 難易度（1-5、Noneの場合はランダム）
            mission_type: 問題タイプ（Noneの場合はランダム）
            max_retries: 最大再試行回数
            verbose: 詳細出力
            source_text: 外部テキスト（RAG用、オプション）
            
        Returns:
            (success, file_path, mission_data)
        """
        if verbose:
            print(f"[INFO] Generating CTF mission with Gemini API...")
            print(f"      Difficulty: {difficulty or 'Random'}")
            print(f"      Type: {mission_type or 'Random'}")
            if source_text:
                print(f"      Source text provided: {len(source_text)} characters")
        
        system_prompt = self._build_system_prompt(source_text=source_text)
        
        for attempt in range(max_retries):
            try:
                user_prompt = self._build_user_prompt(difficulty, mission_type, source_text)
                mission_data = self._generate_with_gemini(system_prompt, user_prompt)
                
                # バリデーション
                mission_id = mission_data.get("mission_id", "UNKNOWN")
                file_path = self.output_dir / f"{mission_id}.json"
                
                # JSONファイルとして保存
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(mission_data, f, indent=2, ensure_ascii=False)
                
                # Validatorで検証
                validator = MissionValidator(mission_data)
                is_valid, errors, warnings = validator.validate_all()
                
                if is_valid:
                    if verbose:
                        print(f"[SUCCESS] Mission generated: {file_path}")
                    return True, str(file_path), mission_data
                else:
                    if verbose:
                        print(f"[WARNING] Validation failed (attempt {attempt + 1}/{max_retries}):")
                        for error in errors:
                            print(f"  - {error}")
                    
                    if attempt < max_retries - 1:
                        continue
                    else:
                        # 最後の試行でも失敗した場合は警告付きで返す
                        if verbose:
                            print(f"[WARNING] Proceeding with validation errors...")
                        return True, str(file_path), mission_data
                        
            except Exception as e:
                if verbose:
                    print(f"[ERROR] Generation failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    return False, None, None
        
        return False, None, None
    
    def regenerate_writeup(self, mission_json: Dict[str, Any], container_url: str, api_key: Optional[str] = None) -> Optional[str]:
        """
        Writeupを再生成（環境非依存のプレースホルダーを使用）
        
        Args:
            mission_json: ミッションJSONデータ
            container_url: 実際のコンテナURL（例: http://localhost:32782）
            api_key: APIキー（オプション）
            
        Returns:
            再生成されたwriteup（Markdown形式）、失敗時はNone
        """
        try:
            # APIキーの設定
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
            else:
                model = self.model
            
            mission_type = mission_json.get("type", "Unknown")
            flag_answer = mission_json.get("flag_answer", "")
            original_writeup = mission_json.get("writeup", "")
            
            # コンテナURLからポート番号を抽出し、環境非依存のプレースホルダーを使用
            # 例: http://localhost:32782 → http://{{CONTAINER_HOST}}:32782
            import re
            port_match = re.search(r':(\d+)$', container_url)
            if port_match:
                port = port_match.group(1)
                placeholder_url = f"http://{{{{CONTAINER_HOST}}}}:{port}"
            else:
                placeholder_url = container_url  # フォールバック
            
            prompt = f"""以下のCTF問題のwriteup（解説）を、プレースホルダーを使用して再生成してください。

**問題タイプ**: {mission_type}
**フラグ**: {flag_answer}
**コンテナURL**: {placeholder_url}
**ポート番号**: {port_match.group(1) if port_match else "不明"}

**重要**: URLには必ず {{{{CONTAINER_HOST}}}} プレースホルダーを使用してください（例: http://{{{{CONTAINER_HOST}}}}:{port_match.group(1) if port_match else "XXXXX"}）

**要件:**
1. **すべて日本語で記述してください**（英語の専門用語は使用可能ですが、説明は日本語）
2. 元のwriteupの内容を保持しつつ、プレースホルダーURL（{placeholder_url}）を反映してください
3. 探索ベースの詳細な解法を含めてください
4. 具体的な手順とコマンドを含めてください（プレースホルダーURLを使用）
5. Markdown形式で出力してください
6. 禁止用語（"Great", "Good luck", "Happy", "Sorry", "Please", "I think", "Feel", "Hope", "!"）を使用しないでください
7. **URLは必ず http://{{{{CONTAINER_HOST}}}}:ポート番号 の形式にしてください**

**元のwriteup（参考）:**
{original_writeup[:500]}...

**出力:**
Markdown形式のwriteupのみを出力してください。JSONやコードブロックは不要です。すべて日本語で記述してください。
"""
            
            _rate_limit()
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=4096,
                )
            )
            
            writeup = response.text.strip()
            
            # コードブロックを除去
            if writeup.startswith("```markdown"):
                writeup = writeup[11:]
            elif writeup.startswith("```"):
                writeup = writeup[3:]
            if writeup.endswith("```"):
                writeup = writeup[:-3]
            writeup = writeup.strip()
            
            return writeup
            
        except Exception as e:
            print(f"[WARNING] Failed to regenerate writeup: {e}", file=sys.stderr)
            return None

