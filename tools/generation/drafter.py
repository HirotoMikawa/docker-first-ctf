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

# Challenge categories (for diversity)
CHALLENGE_CATEGORIES = {
    "WEB_SQLI": {
        "name": "SQL Injection",
        "description": "Classic, Blind, or Time-based SQL Injection",
        "type": "SQLi",
        "tags": ["Web", "SQL", "Database"],
        "file_requirements": ["app.py", "Dockerfile", "requirements.txt"]
    },
    "WEB_XSS": {
        "name": "Cross-Site Scripting",
        "description": "Stored or Reflected XSS vulnerability",
        "type": "XSS",
        "tags": ["Web", "XSS", "JavaScript"],
        "file_requirements": ["app.py", "Dockerfile", "requirements.txt"]
    },
    "WEB_SSRF": {
        "name": "Server-Side Request Forgery",
        "description": "Internal port scanning or local file access",
        "type": "SSRF",
        "tags": ["Web", "SSRF", "Network"],
        "file_requirements": ["app.py", "Dockerfile", "requirements.txt"]
    },
    "WEB_RCE": {
        "name": "Remote Code Execution",
        "description": "Command Injection or Code Execution",
        "type": "RCE",
        "tags": ["Web", "RCE", "Command"],
        "file_requirements": ["app.py", "Dockerfile", "requirements.txt"]
    },
    "CRYPTO_RSA": {
        "name": "RSA Cryptography",
        "description": "Common Modulus, Small Exponent, or Weak Key attacks",
        "type": "Crypto",
        "tags": ["Crypto", "RSA", "Mathematics"],
        "file_requirements": ["chall.py", "output.txt", "Dockerfile"]
    },
    "CRYPTO_CLASSIC": {
        "name": "Classical Cryptography",
        "description": "Caesar, Vigenere, XOR analysis, or Substitution ciphers",
        "type": "Crypto",
        "tags": ["Crypto", "Classical", "Encoding"],
        "file_requirements": ["chall.py", "output.txt", "Dockerfile"]
    },
    "MISC_DOCKER": {
        "name": "Docker Security",
        "description": "Dockerfile analysis, Environment variable hunting, or Container escape",
        "type": "Misconfig",
        "tags": ["Docker", "Container", "Security"],
        "file_requirements": ["Dockerfile", "docker-compose.yml", "README.md"]
    },
    "MISC_LINUX": {
        "name": "Linux Privilege Escalation",
        "description": "SUID binaries, Permission misconfig, or Path hijacking",
        "type": "PrivEsc",
        "tags": ["Linux", "Privilege", "System"],
        "file_requirements": ["setup.sh", "Dockerfile", "README.md"]
    }
}

# Visual themes
VISUAL_THEMES = ["CORPORATE", "UNDERGROUND", "GOVERNMENT", "CYBERPUNK", "MINIMAL"]

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
    
    def _build_system_prompt(self, category: str = None, theme: str = None, category_info: Dict[str, Any] = None) -> str:
        """
        Build system prompt for OpenAI API.
        
        Args:
            category: Challenge category (e.g., "WEB_SQLI")
            theme: Visual theme (e.g., "CORPORATE")
            category_info: Category information dictionary
        """
        # Base prompt
        base_prompt = """あなたは、エリートCTFアーキテクト（CTF Architect）であり、フロントエンドデザイナー（Frontend Designer）です。

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
  "writeup": "# 脆弱性の解説\n\n## 概要\n...\n\n## 解法手順\n...\n\n## 対策方法\n...\n\n## 学んだこと\n...",
  "tags": ["Web", "SQL", "Beginner"],
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

**VERIFICATION CHECKLIST:**
Before submitting your Dockerfile, verify:
- [ ] Every file referenced in `app.py` (via `open()`, `cat`, `sqlite3`, etc.) is created in Dockerfile
- [ ] File paths in `app.py` match file paths in Dockerfile exactly
- [ ] File creation happens BEFORE `USER ctfuser`
- [ ] File permissions allow `ctfuser` to read/write as needed
- [ ] Database files (if any) are initialized with proper schema and data

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

**[CRITICAL: FLAG PLACEMENT STANDARDS - ABSOLUTE REQUIREMENT]**

**⚠️ THIS IS THE MOST IMPORTANT RULE. YOU MUST FOLLOW IT EXACTLY BASED ON THE PROBLEM TYPE. ⚠️**

The flag placement location is determined by the problem type (the "type" field in JSON). You MUST check the problem type and place the flag EXACTLY as specified below.

**DECISION TREE:**
1. If type is "RCE", "LFI", "PrivEsc", or "Misconfig" → Use Rule #1 (FILE at /home/ctfuser/flag.txt)
2. If type is "SQLi", "XSS", "SSRF", "XXE", or "IDOR" → Use Rule #2 (ENV + FILE at /flag.txt)
3. If type is "LogicError" or "Crypto" → Use Rule #3 (CODE or FILE)

**Rule #1: RCE / LFI / PrivEsc / Misconfig Problems**
   - **MANDATORY:** You MUST create a flag file at `/home/ctfuser/flag.txt` (NOT `/flag.txt`).
   - **Dockerfile Instruction (EXACT FORMAT):**
     ```dockerfile
     RUN echo "SolCTF{RANDOM_STRING}" > /home/ctfuser/flag.txt && chmod 644 /home/ctfuser/flag.txt
     ```
   - **CRITICAL:** The path MUST be `/home/ctfuser/flag.txt` (with `/home/ctfuser/` prefix).
   - **CRITICAL:** This MUST be executed BEFORE `USER ctfuser` (as root).
   - **CRITICAL:** The flag value MUST match the `flag_answer` field in the JSON.
   - **Example Dockerfile for RCE:**
     ```dockerfile
     FROM python:3.11-slim
     RUN useradd -m -u 1000 ctfuser
     RUN echo "SolCTF{example_flag}" > /home/ctfuser/flag.txt && chmod 644 /home/ctfuser/flag.txt
     COPY app.py /home/ctfuser/app.py
     RUN pip install Flask==3.0.0 Werkzeug==3.0.0
     USER ctfuser
     WORKDIR /home/ctfuser
     EXPOSE 8000
     CMD ["python", "app.py"]
     ```
   - **Writeup:** Explain that the user needs to read `/home/ctfuser/flag.txt` using the vulnerability (e.g., `cat /home/ctfuser/flag.txt`).

**Rule #2: Web Problems (SQLi / XSS / SSRF / XXE / IDOR)**
   - **MANDATORY:** Set the flag as an environment variable AND a file at `/flag.txt` (root directory).
   - **Dockerfile Instructions (EXACT FORMAT):**
     ```dockerfile
     ENV FLAG="SolCTF{RANDOM_STRING}"
     RUN echo "SolCTF{RANDOM_STRING}" > /flag.txt && chmod 644 /flag.txt
     ```
   - **CRITICAL:** The file path MUST be `/flag.txt` (root directory, NOT `/home/ctfuser/flag.txt`).
   - **CRITICAL:** The flag value MUST match the `flag_answer` field in the JSON.
   - **CRITICAL:** Both `/flag.txt` and `$FLAG` environment variable must contain the same value.
   - **App Code:** The app typically reads from `os.getenv('FLAG')` or a database initialized with this value.
   - **Writeup:** Explain that the user can access the flag through the vulnerability (e.g., SQLi to read from database, or RCE to read `/flag.txt`).

**Rule #3: LogicError / Crypto Problems**
   - **Method:** CODE EMBEDDED or FILE
   - **Requirement:** The flag can be embedded in the code or in a file.
   - **Dockerfile Instruction (if file):**
     ```dockerfile
     RUN echo "SolCTF{RANDOM_STRING}" > /home/ctfuser/flag.txt && chmod 644 /home/ctfuser/flag.txt
     ```
   - **App Code (if embedded):**
     ```python
     FLAG = "SolCTF{RANDOM_STRING}"
     ```

**VERIFICATION CHECKLIST:**
Before submitting your Dockerfile, verify:
- [ ] If type is "RCE", the Dockerfile contains `RUN echo ... > /home/ctfuser/flag.txt` (NOT `/flag.txt`)
- [ ] If type is "SQLi" or other Web types, the Dockerfile contains `RUN echo ... > /flag.txt` (root directory)
- [ ] The flag value in Dockerfile matches the `flag_answer` field exactly
- [ ] The flag file creation happens BEFORE `USER ctfuser`

**[CRITICAL DOCKERFILE USER CREATION]**
- **ユーザー作成は必須**: `USER ctfuser`を使用する前に、必ずユーザーを作成すること。
- **python:3.11-slimの場合**: `RUN useradd -m -u 1000 ctfuser` を使用すること。
  - **重要**: `-s /bin/bash`オプションは使用しないこと。`python:3.11-slim`イメージには`bash`がインストールされていないため、`useradd`コマンドが失敗する可能性がある。
  - 正しい例: `RUN useradd -m -u 1000 ctfuser`
  - 間違った例: `RUN useradd -ms /bin/bash ctfuser`（bashが存在しないため失敗する）
- **alpine:3.19の場合**: `RUN adduser -D -u 1000 ctfuser` を使用すること。
- **順序**: 1) FROM, 2) RUN useradd/adduser（ユーザー作成）, 3) **RUN echo flag > flag.txt（フラグファイル作成）**, 4) COPY files, 5) RUN pip install（rootで実行）, 6) USER ctfuser（ユーザー切り替え）, 7) WORKDIR, 8) EXPOSE, 9) CMD
- **重要**: `USER ctfuser`の前に、必ずユーザー作成コマンド（`RUN useradd`または`RUN adduser`）を実行すること。ユーザーが存在しない状態で`USER ctfuser`を指定すると、コンテナ起動時に「unable to find user ctfuser: no matching entries in passwd file」というエラーが発生する。
- **フラグファイルの権限**: フラグファイルは`ctfuser`が読み取り可能な権限（644）に設定すること。

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

5. **render_template_stringの変数渡し**: `render_template_string()`で変数を使用する場合、必ず`**locals()`または明示的に変数を渡すこと。
   - 正しい例: `render_template_string('Welcome, {{ username }}!', username=user[1])`
   - 正しい例: `render_template_string('Welcome, {{ user[1] }}!', user=user)`
   - 間違った例: `render_template_string('Welcome, {{ user[1] }}!')`（user変数が渡されていない）
   - より安全な方法: `render_template_string('Welcome, {}!'.format(user[1]))`（文字列フォーマットを使用）

6. **SQLi問題の特別な注意事項**:
   - **CRITICAL: データベースの初期化は必須**: SQLi問題では、必ずデータベースにテーブルを作成し、サンプルデータを挿入すること。
   - **データベース初期化の例:**
     ```python
     def init_db():
         conn = sqlite3.connect('database.db')
         conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER, username TEXT, password TEXT)')
         conn.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'admin', 'adminpass')")
         conn.commit()
         conn.close()
     
     # アプリ起動時に初期化
     if __name__ == '__main__':
         init_db()
         app.run(host='0.0.0.0', port=8000)
     ```
   - SQLクエリが複数の結果を返す可能性がある場合（例: `' OR 1=1 -- `）、`fetchone()`の代わりに`fetchall()`を使用し、最初の結果を取得すること。
   - エラーハンドリングを追加して、SQLエラーが発生してもアプリケーションがクラッシュしないようにすること。
   - 正しい例:
     ```python
     try:
         user = conn.execute(query).fetchone()
         if user:
             return render_template_string('Welcome, {}! Flag: {}'.format(user[1], flag))
         else:
             return 'Login failed.'
     except Exception as e:
         return f'Error: {str(e)}'
     ```

7. **RCE問題の特別な注意事項**:
   - **CRITICAL: render_template_stringの変数渡し**: GETリクエストのパラメータ（`request.args.get()`）を使用する場合も、変数を正しく渡すこと。
   - **正しい例（GETリクエスト）:**
     ```python
     @app.route('/run')
     def run_command():
         cmd = request.args.get('cmd')
         if cmd:
             result = os.popen(cmd).read()
             return render_template_string('<pre>{}</pre>'.format(result))
         return 'Command execution is restricted.'
     ```
   - **間違った例:**
     ```python
     @app.route('/run')
     def run_command():
         cmd = request.args.get('cmd')
         if cmd:
             result = os.popen(cmd).read()
             return render_template_string('<pre>{{ result }}</pre>', result=result)  # 変数が渡されていない可能性
         return 'Command execution is restricted.'
     ```
   - **より安全な方法**: 文字列フォーマット（`.format()`）を使用すること。
   - **sudo権限の注意**: `sudo -u root`を使用する場合、ctfuserにsudo権限がないとエラーになる。通常は`os.popen(cmd)`で直接実行すること。

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

**[EDUCATIONAL CONTENT REQUIREMENT]**

1. **writeup (必須・最優先制約)**: 初心者でも完全に再現できる、具体的で詳細なステップバイステップチュートリアル（Writeup）をMarkdown形式で生成すること。
   
   **【最優先】再現可能なコマンドやペイロードを含む、具体的で詳細な手順を必ず含めること:**
   - 抽象的な説明は禁止。必ず具体的なコマンド、ペイロード、スクリプトを含めること。
   - 読者が同じ手順を実行すれば必ず同じ結果が得られること（100%再現可能であること）。
   - **全編日本語で記述すること。** 英語の専門用語は使用可能だが、説明は日本語で行うこと。
   - **コマンドの実行手順を具体的に記述すること。** どのコマンドを実行するか、どのディレクトリで実行するか、どのような結果が得られるかを明確に示すこと。
   - **ブラウザへの入力内容を具体的に記述すること。** どのURLにアクセスするか、どのフォームに何を入力するか、どのボタンをクリックするかを明確に示すこと。
   
   **構造（必須）:**
   - **Introduction（導入）**: 脆弱性とは何か？この問題で学べること（例: "SQL Injectionとは何か？"）
   - **Methodology（解法・最重要）**: この問題を解くための詳細なステップバイステップガイド
     - 使用した正確なペイロードを記載すること（例: `' OR '1'='1`）
     - エクスプロイトが成功したことを確認する出力結果を記載すること（実際の出力例を含める）
     - フラグを取得するための最終的なコマンドまたはスクリプトを記載すること（完全なコマンド例）
     - 各ステップで何をすべきか、どのような結果が期待されるかを明確に示すこと
     - コードブロック（```）を使用して、コマンドやスクリプトを明確に表示すること
   - **Mitigation（緩和策）**: 実際のコードでこの脆弱性を修正する方法（修正前後のコード例を含める）
   - **Key Takeaways（まとめ）**: ユーザーが学んだことを箇条書きでまとめる（3-5個の要点）
   
   **品質要件（絶対遵守）:**
   - **再現性（最優先）**: 読者が同じ手順を実行すれば必ず同じ結果が得られること。具体的なコマンド、ペイロード、出力例を含めること。
   - **具体性（必須）**: 抽象的な説明ではなく、具体的なコマンド、ペイロード、出力例を含めること。
   - **完全性（必須）**: 最初から最後まで、すべてのステップを網羅すること。
   - **日本語記述（必須）**: 全編日本語で記述すること。コマンドの実行手順やブラウザへの入力内容を具体的に記述すること。
   
   - 例: `"writeup": "# SQL Injection Explained\n\n## Introduction\nSQL Injectionとは...\n\n## Methodology\n### Step 1: 情報収集\nまず、以下のコマンドで...\n\n```bash\ncurl http://target.com/search?q=test'\n```\n\n出力:\n```\nError: syntax error near 'test''\n```\n\n### Step 2: ペイロードの構築\n...\n\n## Mitigation\n修正前:\n```python\nquery = f\"SELECT * FROM users WHERE id = {user_id}\"\n```\n\n修正後:\n```python\nquery = \"SELECT * FROM users WHERE id = %s\"\ncursor.execute(query, (user_id,))\n```\n\n## Key Takeaways\n- SQL Injectionは...\n- 対策として...\n"`

**[EXECUTION ENVIRONMENT PRIORITY]**

1. **If the methodology is simple (e.g., SQLi, XSS, basic IDOR), YOU MUST explain the step using BROWSER INPUT first.**
   - For SQL Injection: "Step 1: ブラウザでログインページを開き、ユーザー名フォームに `admin' -- ` と入力します。"
   - For XSS: "Step 1: ブラウザでコメントフォームを開き、メッセージ欄に `<script>alert('XSS')</script>` と入力します。"
   - For IDOR: "Step 1: ブラウザのURLバーで、`/user?id=1` を `/user?id=2` に変更してアクセスします。"
   - **優先順位**: ブラウザでの操作説明を最初に記載し、その後で必要に応じてCURLコマンドを補足として記載すること。

2. **If a POST request or complex data is required (like in SSRF, XXE, or advanced RCE cases):**
   - You MUST provide the full CURL command with complete headers and payload.
   - You MUST also provide an explanation on how to use tools like **Browser Developer Tools (Network tab)** or a proxy like **Burp Suite** to manually send the POST request.
   - Alternatively, mention how to create a simple HTML form for testing (より高度な学習内容として組み込む).
   - Example: "Step 1: ブラウザの開発者ツール（F12）を開き、Networkタブを選択します。フォームを送信し、リクエストを確認します。または、以下のCURLコマンドを使用します："
   - Example: "Step 1: Burp Suiteなどのプロキシツールを使用してリクエストをインターセプトし、ペイロードを変更します。または、以下のCURLコマンドを使用します："

3. **When using CURL commands:**
   - You MUST clearly state that the user should execute the command in their own terminal.
   - You MUST clearly state that the user should replace the placeholder URL (e.g., `http://localhost:8000` or `http://{{CONTAINER_HOST}}`) with their assigned mission URL (e.g., `http://localhost:32804`).
   - Example: "**注意**: 以下のコマンドを実行する際は、`http://localhost:8000` を実際のミッションURL（例: `http://localhost:32804`）に置き換えてください。"
   - Example: "**実行方法**: ターミナルで以下のコマンドを実行します。URLは実際のミッションURLに置き換えてください："

2. **tags (必須)**: 問題の種類や難易度を表すタグの配列を生成すること。
   - 例: `["Web", "SQL", "Beginner"]`, `["Network", "RCE", "Advanced"]`
   - カテゴリ（Web, Network, Crypto等）、脆弱性タイプ（SQL, RCE, SSRF等）、難易度（Beginner, Intermediate, Advanced等）を含めること
   - 2-4個のタグを推奨

**[SOLVER SCRIPT REQUIREMENT]**

You MUST also generate a solver script (Python) that demonstrates how to solve this challenge.
- The solver script should be included in the `metadata` field as `solver_script`.
- Format: `"metadata": {{ "solver_script": "# Python solver script\\nimport ...\\n# Solution code here" }}`
- This is for internal validation and quality assurance.

**重要**: 
- JSONには必ず `"flag_answer": "SolCTF{...}"` を含めること。
- JSONには必ず `"files"` オブジェクトを含め、実際に動作するアプリケーションコードを生成すること。
- JSONには必ず `"writeup"` フィールドを含め、初心者にもわかりやすい解説記事を生成すること。
- JSONには必ず `"tags"` フィールドを含め、問題の種類や難易度を表すタグの配列を生成すること。
- JSONには必ず `"metadata"` フィールドに `"solver_script"` を含め、解法スクリプトを生成すること。"""
        
        return base_prompt
    
    def _build_user_prompt(self, difficulty: Optional[int] = None, mission_type: Optional[str] = None, category: Optional[str] = None, theme: Optional[str] = None, category_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Build user prompt for OpenAI API.
        
        Args:
            difficulty: Target difficulty (1-5)
            mission_type: Mission type
            category: Challenge category
            theme: Visual theme
            category_info: Category information dictionary
        """
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
        
        # Category-specific prompt
        category_prompt = ""
        flag_placement_reminder = ""
        if category and category_info:
            mission_type = category_info.get('type', 'Unknown')
            # Add flag placement reminder based on problem type
            if mission_type in ["RCE", "LFI", "PrivEsc", "Misconfig"]:
                flag_placement_reminder = f"""
**⚠️ CRITICAL FLAG PLACEMENT REMINDER FOR {mission_type} PROBLEMS:**
- You MUST place the flag at `/home/ctfuser/flag.txt` (NOT `/flag.txt`).
- Dockerfile MUST contain: `RUN echo "SolCTF{{...}}" > /home/ctfuser/flag.txt && chmod 644 /home/ctfuser/flag.txt`
- This is a MANDATORY requirement. Do NOT use `/flag.txt` for {mission_type} problems.
"""
            elif mission_type in ["SQLi", "XSS", "SSRF", "XXE", "IDOR"]:
                flag_placement_reminder = f"""
**⚠️ CRITICAL FLAG PLACEMENT REMINDER FOR {mission_type} PROBLEMS:**
- You MUST place the flag at `/flag.txt` (root directory) AND set ENV FLAG variable.
- Dockerfile MUST contain: `ENV FLAG="SolCTF{{...}}"` AND `RUN echo "SolCTF{{...}}" > /flag.txt && chmod 644 /flag.txt`
- This is a MANDATORY requirement. Do NOT use `/home/ctfuser/flag.txt` for {mission_type} problems.
"""
            
            category_prompt = f"""
**必須カテゴリ:** {category_info['name']} ({category})
**カテゴリ説明:** {category_info['description']}
**必須タグ:** {', '.join(category_info['tags'])}
**視覚テーマ:** {theme}
**問題タイプ:** {mission_type}

{flag_placement_reminder}

このカテゴリに厳密に従って問題を作成してください。他のカテゴリ（例: SQL Injection）は使用しないでください。
"""
        
        prompt = f"""難易度 {difficulty} ({difficulty_descriptions[difficulty]}) のCTF問題を1つ作成してください。

{category_prompt}

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
- **必ず `writeup` フィールドを含め、初心者でも完全に再現できる、具体的で詳細なステップバイステップチュートリアル（Markdown形式）を生成すること**
  - **【最優先】再現可能なコマンドやペイロードを含む、具体的で詳細な手順を必ず含めること**
  - **全編日本語で記述すること。** 英語の専門用語は使用可能だが、説明は日本語で行うこと。
  - **コマンドの実行手順を具体的に記述すること。** どのコマンドを実行するか、どのディレクトリで実行するか、どのような結果が得られるかを明確に示すこと。
  - **ブラウザへの入力内容を具体的に記述すること。** どのURLにアクセスするか、どのフォームに何を入力するか、どのボタンをクリックするかを明確に示すこと。
  - Introduction: 脆弱性とは何か？
  - Methodology: ステップバイステップの解法ガイド（具体的なコマンド、ペイロード、出力例を含める）
  - Mitigation: 実際のコードで修正する方法（修正前後のコード例を含める）
  - Key Takeaways: 学んだことを箇条書きでまとめる
- **必ず `tags` フィールドを含め、問題の種類や難易度を表すタグの配列（2-4個）を生成すること**
  - カテゴリ（Web, Network, Crypto等）、脆弱性タイプ（SQL, RCE, SSRF等）、難易度（Beginner, Intermediate, Advanced等）を含めること
- 生成されるコードは、PROJECT_MASTER.mdのセキュリティ基準（非root実行、ポート8000のみ公開）を守ること
- JSON形式のみで返答すること"""
        
        return prompt
    
    def _fix_flag_placement(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process mission JSON to fix flag placement if incorrect.
        
        Args:
            mission: Mission JSON dictionary
            
        Returns:
            Fixed mission JSON dictionary
        """
        problem_type = mission.get("type", "").upper()
        flag_answer = mission.get("flag_answer", "")
        files = mission.get("files", {})
        dockerfile = files.get("Dockerfile", "")
        
        if not dockerfile or not flag_answer:
            return mission
        
        # Rule #1: RCE / LFI / PrivEsc / Misconfig → /home/ctfuser/flag.txt
        if problem_type in ["RCE", "LFI", "PRIVESC", "MISCONFIG"]:
            # Check if flag is incorrectly placed at /flag.txt
            if "/flag.txt" in dockerfile and "/home/ctfuser/flag.txt" not in dockerfile:
                # Fix: Replace /flag.txt with /home/ctfuser/flag.txt
                import re
                # Replace RUN echo ... > /flag.txt with /home/ctfuser/flag.txt
                dockerfile = re.sub(
                    r'RUN\s+echo\s+"([^"]+)"\s+>\s+/flag\.txt',
                    rf'RUN echo "\1" > /home/ctfuser/flag.txt',
                    dockerfile
                )
                dockerfile = re.sub(
                    r'RUN\s+echo\s+([^\s>]+)\s+>\s+/flag\.txt',
                    r'RUN echo \1 > /home/ctfuser/flag.txt',
                    dockerfile
                )
                # Ensure chmod is also updated
                if "chmod" in dockerfile and "/home/ctfuser/flag.txt" in dockerfile:
                    dockerfile = re.sub(
                        r'chmod\s+\d+\s+/flag\.txt',
                        'chmod 644 /home/ctfuser/flag.txt',
                        dockerfile
                    )
                files["Dockerfile"] = dockerfile
                mission["files"] = files
                logger.info(f"Fixed flag placement for {problem_type}: moved from /flag.txt to /home/ctfuser/flag.txt")
        
        # Rule #2: Web problems (SQLi / XSS / SSRF / XXE / IDOR) → /flag.txt + ENV
        elif problem_type in ["SQLI", "XSS", "SSRF", "XXE", "IDOR"]:
            # Check if flag is incorrectly placed at /home/ctfuser/flag.txt
            if "/home/ctfuser/flag.txt" in dockerfile and "/flag.txt" not in dockerfile:
                # Fix: Replace /home/ctfuser/flag.txt with /flag.txt
                import re
                # Replace RUN echo ... > /home/ctfuser/flag.txt with /flag.txt
                dockerfile = re.sub(
                    r'RUN\s+echo\s+"([^"]+)"\s+>\s+/home/ctfuser/flag\.txt',
                    rf'RUN echo "\1" > /flag.txt',
                    dockerfile
                )
                dockerfile = re.sub(
                    r'RUN\s+echo\s+([^\s>]+)\s+>\s+/home/ctfuser/flag\.txt',
                    r'RUN echo \1 > /flag.txt',
                    dockerfile
                )
                # Ensure ENV FLAG is set
                if "ENV FLAG" not in dockerfile and "ENV FLAG=" not in dockerfile:
                    # Add ENV FLAG before the RUN echo command
                    flag_value = flag_answer
                    env_line = f'ENV FLAG="{flag_value}"\n'
                    # Find the line with RUN echo ... > /flag.txt and add ENV before it
                    lines = dockerfile.split('\n')
                    new_lines = []
                    env_added = False
                    for line in lines:
                        if not env_added and "RUN echo" in line and "/flag.txt" in line:
                            new_lines.append(env_line)
                            env_added = True
                        new_lines.append(line)
                    dockerfile = '\n'.join(new_lines)
                files["Dockerfile"] = dockerfile
                mission["files"] = files
                logger.info(f"Fixed flag placement for {problem_type}: moved from /home/ctfuser/flag.txt to /flag.txt and added ENV FLAG")
        
        return mission
    
    def _fix_database_initialization(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process mission JSON to fix database initialization for SQLi problems.
        
        Args:
            mission: Mission JSON dictionary
            
        Returns:
            Fixed mission JSON dictionary
        """
        problem_type = mission.get("type", "").upper()
        files = mission.get("files", {})
        app_code = files.get("app.py", "")
        
        if problem_type != "SQLI" or not app_code:
            return mission
        
        # Check if database initialization exists
        has_init = (
            "CREATE TABLE" in app_code or
            "init_db" in app_code or
            "initialize" in app_code.lower()
        )
        
        # Check if sqlite3 is used
        uses_sqlite = "sqlite3" in app_code
        
        if uses_sqlite and not has_init:
            # Add database initialization
            import re
            
            # Find the main block
            if "if __name__ == '__main__':" in app_code:
                # Add init_db function before the main block
                init_function = """
def init_db():
    import sqlite3
    conn = sqlite3.connect('database.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER, username TEXT, password TEXT)')
    conn.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'admin', 'adminpass')")
    conn.commit()
    conn.close()
"""
                
                # Insert init_db function before the main block
                app_code = app_code.replace(
                    "if __name__ == '__main__':",
                    f"{init_function}\nif __name__ == '__main__':"
                )
                
                # Add init_db() call in the main block
                if "app.run(" in app_code:
                    app_code = re.sub(
                        r'(if __name__ == \'__main__\':\s*\n\s*)app\.run\(',
                        r'\1init_db()\n    app.run(',
                        app_code
                    )
                
                files["app.py"] = app_code
                mission["files"] = files
                logger.info("Fixed database initialization for SQLi problem: added init_db() function")
        
        return mission
    
    def _fix_render_template_string(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process mission JSON to fix render_template_string issues.
        
        Args:
            mission: Mission JSON dictionary
            
        Returns:
            Fixed mission JSON dictionary
        """
        files = mission.get("files", {})
        app_code = files.get("app.py", "")
        
        if not app_code:
            return mission
        
        import re
        fixed_code = app_code
        
        # Fix: render_template_string with {{ variable }} but variable not passed correctly
        # Convert to .format() method which is more reliable
        # Pattern: render_template_string('...{{ result }}...', result=result) -> render_template_string('...{}...'.format(result))
        patterns_to_fix = [
            (r"render_template_string\s*\(\s*'([^']*)\{\{\s*result\s*\}\}([^']*)'\s*,\s*result\s*=\s*result\s*\)",
             r"render_template_string('\1{}\2'.format(result))"),
            (r"render_template_string\s*\(\s*'([^']*)\{\{\s*output\s*\}\}([^']*)'\s*,\s*output\s*=\s*output\s*\)",
             r"render_template_string('\1{}\2'.format(output))"),
            (r"render_template_string\s*\(\s*'([^']*)\{\{\s*user\s*\}\}([^']*)'\s*,\s*user\s*=\s*user\s*\)",
             r"render_template_string('\1{}\2'.format(user))"),
        ]
        
        for pattern, replacement in patterns_to_fix:
            if re.search(pattern, fixed_code):
                fixed_code = re.sub(pattern, replacement, fixed_code)
                logger.info("Fixed render_template_string: converted to .format() method")
        
        # Fix: Remove sudo -u root (ctfuser doesn't have sudo permissions)
        if "sudo -u root" in fixed_code:
            # Replace various patterns of sudo -u root
            fixed_code = re.sub(
                r"os\.popen\(f?'sudo -u root \{command\}'\)",
                "os.popen(command)",
                fixed_code
            )
            fixed_code = re.sub(
                r"os\.popen\(f?'sudo -u root \{cmd\}'\)",
                "os.popen(cmd)",
                fixed_code
            )
            fixed_code = re.sub(
                r"os\.popen\(f?\"sudo -u root \{command\}\"\)",
                "os.popen(command)",
                fixed_code
            )
            fixed_code = re.sub(
                r"os\.popen\(f?\"sudo -u root \{cmd\}\"\)",
                "os.popen(cmd)",
                fixed_code
            )
            # Also handle cases without f-string
            fixed_code = re.sub(
                r"os\.popen\('sudo -u root ' \+ command\)",
                "os.popen(command)",
                fixed_code
            )
            fixed_code = re.sub(
                r"os\.popen\('sudo -u root ' \+ cmd\)",
                "os.popen(cmd)",
                fixed_code
            )
            if "sudo -u root" not in fixed_code:
                logger.info("Fixed: Removed sudo -u root (ctfuser doesn't have sudo permissions)")
        
        if fixed_code != app_code:
            files["app.py"] = fixed_code
            mission["files"] = files
        
        return mission
    
    def _extract_visible_html(self, app_code: str) -> str:
        """
        Extract HTML that would be visible to an attacker (without source code access).
        
        Args:
            app_code: Python application code
            
        Returns:
            HTML content visible to attacker
        """
        import re
        
        # Extract HTML from render_template_string calls
        html_parts = []
        
        # Pattern 1: render_template_string('''...''')
        pattern1 = r"render_template_string\s*\(\s*'''([^']+)'''"
        matches = re.findall(pattern1, app_code, re.DOTALL)
        html_parts.extend(matches)
        
        # Pattern 2: render_template_string("""...""")
        pattern2 = r'render_template_string\s*\(\s*"""([^"]+)"""'
        matches = re.findall(pattern2, app_code, re.DOTALL)
        html_parts.extend(matches)
        
        # Pattern 3: return '''...'''
        pattern3 = r"return\s+'''([^']+)'''"
        matches = re.findall(pattern3, app_code, re.DOTALL)
        html_parts.extend(matches)
        
        # Pattern 4: return """..."""
        pattern4 = r'return\s+"""([^"]+)"""'
        matches = re.findall(pattern4, app_code, re.DOTALL)
        html_parts.extend(matches)
        
        if html_parts:
            return '\n\n---\n\n'.join(html_parts)
        else:
            return "HTML情報を抽出できませんでした。実際のコンテナにアクセスして確認してください。"
    
    def _generate_with_ai(self, difficulty: Optional[int] = None, mission_type: Optional[str] = None, category: Optional[str] = None, theme: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate mission JSON using OpenAI API.
        
        Args:
            difficulty: Target difficulty (1-5). If None, random.
            mission_type: Target mission type. If None, random.
            category: Challenge category (e.g., "WEB_SQLI", "CRYPTO_RSA"). If None, random.
            theme: Visual theme (e.g., "CORPORATE", "UNDERGROUND"). If None, random.
            
        Returns:
            Mission JSON dictionary
            
        Raises:
            Exception: If API call fails
        """
        # Select category and theme if not provided
        if category is None or category not in CHALLENGE_CATEGORIES:
            category = random.choice(list(CHALLENGE_CATEGORIES.keys()))
        
        if theme is None or theme not in VISUAL_THEMES:
            theme = random.choice(VISUAL_THEMES)
        
        # Get category info
        category_info = CHALLENGE_CATEGORIES[category]
        
        # Override mission_type if category specifies it
        if mission_type is None:
            mission_type = category_info["type"]
        
        system_prompt = self._build_system_prompt(category, theme, category_info)
        user_prompt = self._build_user_prompt(difficulty, mission_type, category, theme, category_info)
        
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
            
            # Post-process: Fix flag placement if incorrect
            mission = self._fix_flag_placement(mission)
            
            # Post-process: Fix database initialization for SQLi problems
            mission = self._fix_database_initialization(mission)
            
            # Post-process: Fix render_template_string issues for RCE problems
            mission = self._fix_render_template_string(mission)
            
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
                    # For python:3.11-slim, use useradd without -s /bin/bash (bash may not be installed)
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
            
            # Ensure writeup is present (generate fallback if missing)
            if "writeup" not in mission or not mission.get("writeup"):
                mission_type = mission.get("type", "Unknown")
                fallback_writeup = f"""# {mission_type} Vulnerability Explained

## What is it?

This challenge demonstrates a {mission_type} vulnerability. Learn how to identify and exploit this security flaw.

## Solution Steps

1. Identify the vulnerability point
2. Craft an exploit payload
3. Extract the flag

## Mitigation

To fix this vulnerability in real code, ensure proper input validation and sanitization.

## Key Takeaways

- Understanding {mission_type} vulnerabilities
- Practical exploitation techniques
- Security best practices"""
                mission["writeup"] = fallback_writeup
            
            # Ensure tags are present (generate fallback if missing)
            if "tags" not in mission or not mission.get("tags"):
                # Extract tags from environment if available
                if "environment" in mission and "tags" in mission["environment"]:
                    mission["tags"] = mission["environment"]["tags"]
                else:
                    # Generate default tags based on type and difficulty
                    mission_type = mission.get("type", "Unknown")
                    difficulty = mission.get("difficulty", 3)
                    
                    type_tags = {
                        "SQLi": ["Web", "SQL"],
                        "RCE": ["Web", "RCE"],
                        "SSRF": ["Web", "Network"],
                        "XXE": ["Web", "XML"],
                        "IDOR": ["Web", "Auth"],
                        "PrivEsc": ["Linux", "Privilege"],
                        "LogicError": ["Web", "Logic"],
                        "Misconfig": ["Web", "Config"]
                    }
                    
                    difficulty_tags = {
                        1: "Beginner",
                        2: "Beginner",
                        3: "Intermediate",
                        4: "Advanced",
                        5: "Expert"
                    }
                    
                    tags = type_tags.get(mission_type, ["Web", "Security"])
                    tags.append(difficulty_tags.get(difficulty, "Intermediate"))
                    mission["tags"] = tags
            
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
    
    def regenerate_writeup(self, mission_json: Dict[str, Any], container_url: str, api_key: Optional[str] = None) -> Optional[str]:
        """
        Regenerate writeup with actual container URL.
        
        Args:
            mission_json: Mission JSON dictionary
            container_url: Actual container URL (e.g., "http://localhost:32804")
            api_key: OpenAI API key (if None, uses instance key)
            
        Returns:
            New writeup content or None on failure
        """
        if api_key:
            client = OpenAI(api_key=api_key)
        else:
            client = self.client
        
        mission_type = mission_json.get("type", "Unknown")
        mission_id = mission_json.get("mission_id", "UNKNOWN")
        flag_answer = mission_json.get("flag_answer", "")
        
        system_prompt = """あなたは、CTF問題の解説記事を書く専門家です。

実際に動作するコンテナのURLを使って、初心者でも完全に再現できる、具体的で詳細なステップバイステップチュートリアル（Writeup）をMarkdown形式で生成してください。

**重要な制約:**
1. 実際のコンテナURL（例: http://localhost:32804）を使用すること
2. 全編日本語で記述すること
3. 再現可能なコマンドやペイロードを含む、具体的で詳細な手順を必ず含めること
4. ブラウザでの操作説明を優先し、必要に応じてCURLコマンドを補足として記載すること
5. 各ステップで何をすべきか、どのような結果が期待されるかを明確に示すこと
6. **解説のボリュームは多めにすること** - 読者がいろいろ試せるように、複数のアプローチや手順を紹介すること
7. **適切な位置で改行すること** - 見やすくするため、段落を適切に分けること

**[CRITICAL: EXPLORATION-BASED METHODOLOGY - 探索ベースの解法]**

**最重要:** 解説は「基本形から始めて、探索を通じて発見する」形式で記述すること。

1. **基本形の操作から始める:**
   - まず、最も基本的で直感的な操作を試す（例: `ls`、`cat flag.txt`、`cat /flag.txt`）
   - この操作の結果（成功または失敗）を記載する
   - 成功した場合と失敗した場合の両方のシナリオを想定する

2. **失敗した場合の探索プロセス（重要）:**
   - 基本形の操作が失敗した場合、なぜ失敗したのかを考える
   - 現在の状況を確認する（例: `pwd`で現在のディレクトリを確認）
   - 周辺を探索する（例: 親ディレクトリを見る、他のディレクトリを確認する）
   - **複数の探索手順を紹介する** - 読者がいろいろ試せるように
   - 段階的に探索範囲を広げる
   - 各探索ステップで「なぜこの操作が必要なのか」を説明する

3. **発見と解決:**
   - 探索を通じてフラグの場所を発見する
   - なぜその場所にあるのかを説明する
   - **最終的なフラグ取得方法を記載する（フラグそのものではなく、操作手順）**
   - 「これで一応回答がゲットできます」という形で記載する

4. **環境情報の説明（重要）:**
   - **裏でデータベースなどの情報がどうなっているのかを明記する**
   - 例: 「この問題では、SQLiteデータベースが使用されており、`users`テーブルには`admin`ユーザーが登録されています」
   - 例: 「フラグは`/home/ctfuser/flag.txt`に配置されており、ctfuser権限で読み取り可能です」
   - **構築された環境から、このコマンドでこの情報を抜いていたり、この場所にアクセスしていたりするという説明を追加**
   - 例: 「`cat /home/ctfuser/flag.txt`コマンドを実行することで、ctfuserのホームディレクトリに配置されたフラグファイルにアクセスできます」

5. **教育的価値の説明:**
   - 「基本形から少し形が変わっている」ことを明示する
   - 「追加の操作が必要な理由」を説明する
   - 「探索の重要性」を強調する

**構造（詳細版）:**
- Introduction: 脆弱性とは何か？この問題で学べること
- Environment Overview: 環境情報（データベース、ファイル構造、権限など）
- Methodology: ステップバイステップの解法ガイド
  - **Step 1: 基本形の操作を試す**（例: `ls`、`cat flag.txt`）
    - 結果: 成功または失敗
  - **Step 2: 失敗した場合の探索（複数の手順を紹介）**
    - 手順A: `pwd`で現在地を確認
    - 手順B: `ls /`でルートディレクトリを確認
    - 手順C: `ls /home`でホームディレクトリを確認
    - 手順D: `ls /home/ctfuser`でユーザーディレクトリを確認
    - 各手順で「なぜこの操作が必要なのか」を説明
  - **Step 3: 発見と解決**
    - フラグの場所を発見
    - 最終的なフラグ取得方法を記載（フラグそのものではなく、操作手順）
    - 「これで一応回答がゲットできます」という形で記載
- Mitigation: 実際のコードで修正する方法
- Key Takeaways: 学んだことを箇条書きでまとめる

**出力形式:**
Markdown形式の文字列のみを返してください。JSONやその他の形式は不要です。
**適切な位置で改行し、見やすくすること。**"""
        
        # Extract actual code to analyze flag location
        files = mission_json.get("files", {})
        app_code = files.get("app.py", "")
        dockerfile = files.get("Dockerfile", "")
        
        # Analyze how flag is accessed
        flag_location_hint = ""
        if "CTF_FLAG" in app_code or "os.getenv" in app_code or "environ" in app_code:
            flag_location_hint = "フラグは環境変数CTF_FLAGとして設定されています。コード内でos.getenv('CTF_FLAG')またはos.environ['CTF_FLAG']で取得されている可能性があります。"
        elif "flag.txt" in dockerfile and "COPY flag.txt" in dockerfile:
            flag_location_hint = "フラグはflag.txtファイルとして配置されています。"
        elif "flag.txt" in files:
            flag_location_hint = "フラグはflag.txtファイルとして定義されていますが、Dockerfileでコピーされていない可能性があります。実際のコードを確認して、フラグの取得方法を特定してください。"
        else:
            flag_location_hint = "フラグの配置場所をコードから確認してください。環境変数、ファイル、データベース、またはAPIエンドポイントのいずれかに配置されている可能性があります。"
        
        user_prompt = f"""以下のCTF問題の解説記事を生成してください。

**重要: 解く側の視点で解説を生成すること**
- 解く側は**ソースコードを見ることができません**
- 解く側が見える情報は、**ブラウザで表示されるHTMLとレスポンスのみ**です
- コード内の変数名（例: SECRET_MESSAGE）や実装詳細は、解く側には見えません
- 解説には、**実際にブラウザで見える情報のみ**を基にした解法を記載してください

**[CRITICAL: EXPLORATION-BASED METHODOLOGY - 探索ベースの解法]**

**最重要:** 解説は「基本形から始めて、探索を通じて発見する」形式で記述すること。

1. **基本形の操作から始める:**
   - まず、最も基本的で直感的な操作を試す
   - 例（RCE問題）: `ls`を実行して、現在のディレクトリの内容を確認
   - 例（SQLi問題）: 基本的なログイン試行
   - この操作が成功する場合と失敗する場合の両方を想定する

2. **失敗した場合の探索プロセス:**
   - 基本形の操作が失敗した場合、なぜ失敗したのかを考える
   - 現在の状況を確認する（例: `pwd`で現在のディレクトリを確認）
   - 周辺を探索する（例: 親ディレクトリを見る、他のディレクトリを確認する）
   - 段階的に探索範囲を広げる
   - 例（RCE問題）:
     - `ls`でファイルが見つからない
     - `pwd`で現在地を確認（例: `/home/ctfuser`）
     - `ls /`でルートディレクトリを確認
     - `ls /home`でホームディレクトリを確認
     - `ls /home/ctfuser`でユーザーディレクトリを確認
     - `cat /home/ctfuser/flag.txt`でフラグを取得

3. **発見と解決:**
   - 探索を通じてフラグの場所を発見する
   - なぜその場所にあるのかを説明する
   - 最終的なフラグ取得方法を記載する

4. **教育的価値の説明:**
   - 「基本形から少し形が変わっている」ことを明示する
   - 「追加の操作が必要な理由」を説明する
   - 「探索の重要性」を強調する
   - 例: 「この問題は、基本的な`ls`コマンドだけではフラグファイルが見つからないように設計されています。これは、CTF問題でよく見られる『探索が必要な問題』の一例です。実際のセキュリティ調査でも、最初の試行が失敗した場合、周辺を探索して情報を収集することが重要です。」

**問題情報:**
- タイプ: {mission_type}
- ミッションID: {mission_id}
- コンテナURL（参考）: {container_url}
- フラグ: {flag_answer}

**解く側が見える情報（HTML）:**
以下は、解く側がブラウザで実際に見ることができる情報です。この情報のみを基に解説を生成してください。
```
{self._extract_visible_html(app_code) if app_code else "HTML情報が取得できませんでした"}
```

**注意事項:**
- 「コードを見るとわかる」という記述は**絶対に使用しないこと**
- コード内の変数名や実装詳細を説明に含めないこと
- 解く側が実際にブラウザで見える情報のみを基にした解法を記載すること
- 推測や試行錯誤のプロセスを含めること（例: 「様々なキーを試してみる」「HTMLを確認してヒントを探す」）

**Dockerfile:**
```
{dockerfile[:1000] if len(dockerfile) > 1000 else dockerfile}
```

**フラグの配置に関する情報:**
{flag_location_hint}

**既存のwriteup（参考）:**
{mission_json.get('writeup', 'なし')}

初心者でも完全に再現できる、具体的で詳細なステップバイステップチュートリアルを生成してください。

**[CRITICAL: EXPLORATION-BASED METHODOLOGY - 探索ベースの解法]**

**最重要:** 解説は「基本形から始めて、探索を通じて発見する」形式で記述すること。

1. **基本形の操作から始める:**
   - まず、最も基本的で直感的な操作を試す
   - 例（RCE問題）: `ls`を実行して、現在のディレクトリの内容を確認
   - 例（SQLi問題）: 基本的なログイン試行
   - この操作の結果（成功または失敗）を記載する

2. **失敗した場合の探索プロセス（重要）:**
   - 基本形の操作が失敗した場合、なぜ失敗したのかを考える
   - 現在の状況を確認する（例: `pwd`で現在のディレクトリを確認）
   - 周辺を探索する（例: 親ディレクトリを見る、他のディレクトリを確認する）
   - 段階的に探索範囲を広げる
   - **各探索ステップで「なぜこの操作が必要なのか」を説明する**
   - 例（RCE問題で`ls`でファイルが見つからない場合）:
     ```
     Step 1: 基本形の操作を試す
     - `ls`を実行
     - 結果: app.py と requirements.txt しか表示されない（flag.txtが見つからない）
     
     Step 2: 現在の状況を確認
     - `pwd`を実行して現在のディレクトリを確認
     - 結果: /home/ctfuser にいることがわかる
     
     Step 3: 周辺を探索
     - `ls /`でルートディレクトリを確認
     - `ls /home`でホームディレクトリを確認
     - `ls /home/ctfuser`でユーザーディレクトリを再確認
     - 結果: /home/ctfuser/flag.txt が見つかる
     
     Step 4: フラグを取得
     - `cat /home/ctfuser/flag.txt`でフラグを取得
     ```

3. **教育的価値の説明:**
   - 「この問題は、基本的な`ls`コマンドだけではフラグファイルが見つからないように設計されています」
   - 「これは、CTF問題でよく見られる『探索が必要な問題』の一例です」
   - 「実際のセキュリティ調査でも、最初の試行が失敗した場合、周辺を探索して情報を収集することが重要です」
   - 「基本形から少し形が変わっているため、追加の操作（探索）が必要になります」

**[CRITICAL: 解説のボリュームと構成]**

**最重要:** 解説は**ボリュームを多めに**し、読者が**いろいろ試せる**ようにすること。

1. **環境情報セクションを追加:**
   - データベースの構造（テーブル名、カラム名、サンプルデータ）
   - ファイル構造（フラグの配置場所、権限）
   - アプリケーションの構成（エンドポイント、パラメータ名）
   - 例: 「この問題では、SQLiteデータベース（`database.db`）が使用されています。`users`テーブルには以下のデータが登録されています：
     - id: 1, username: 'admin', password: 'adminpass'
     - id: 2, username: 'user', password: 'userpass'
   フラグは環境変数`FLAG`として設定されており、値は`SolCTF{...}`です。」

2. **複数の探索手順を紹介:**
   - 基本形の操作から始める
   - 失敗した場合の複数の探索手順を紹介
   - 各手順で「なぜこの操作が必要なのか」を説明
   - 読者がいろいろ試せるように、複数のアプローチを提示

3. **最終的なフラグ取得方法:**
   - **フラグそのものではなく、フラグが獲得できる最終的な操作を記載**
   - 「これで一応回答がゲットできます」という形で記載
   - 例: 「`cat /home/ctfuser/flag.txt`コマンドを実行することで、フラグを取得できます。これで一応回答がゲットできます。」

4. **環境と操作の関連性を説明:**
   - **構築された環境から、このコマンドでこの情報を抜いていたり、この場所にアクセスしていたりするという説明を追加**
   - 例: 「この問題では、フラグが`/home/ctfuser/flag.txt`に配置されています。`cat /home/ctfuser/flag.txt`コマンドを実行することで、このファイルにアクセスし、フラグを取得できます。このファイルは、Dockerfileの`RUN echo ... > /home/ctfuser/flag.txt`コマンドで作成されています。」

5. **適切な改行:**
   - 見やすくするため、適切な位置で改行すること
   - 段落を適切に分けること
   - コードブロックの前後には空行を入れること

**重要な制約:**
- **実際のコード（app.py）を確認して、フラグの取得方法を正確に特定すること**
  - コード内でフラグがどのように取得されているか（環境変数、ファイル、APIエンドポイントなど）を確認
  - フラグが存在しない場所（例: flag.txtファイル）を指定しないこと
  - 実際のコードに基づいて、正確なフラグ取得手順を記載すること
- **URLの部分は必ず `{{CONTAINER_HOST}}` というプレースホルダーを使用すること**
  - 例: `http://{{CONTAINER_HOST}}/debug` や `curl http://{{CONTAINER_HOST}}/api/flag`
  - 実際のURL（{container_url}）や内部IPアドレス（192.168.x.x や 172.x.x.x）は使用しないこと
  - このプレースホルダーは、ユーザーが問題をINITIALIZEした際に実際のポート番号に置き換えられます
- ブラウザでの操作説明を優先すること
- 全編日本語で記述すること
- 再現可能なコマンドやペイロードを含む、具体的で詳細な手順を必ず含めること
- **コードに基づいて、実際に動作する手順のみを記載すること**
- **解説のボリュームは多めにすること** - 読者がいろいろ試せるように、複数のアプローチや手順を紹介すること"""
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            new_writeup = response.choices[0].message.content.strip()
            return new_writeup
            
        except Exception as e:
            print(f"[ERROR] Failed to regenerate writeup: {e}", file=sys.stderr)
            return None
    
    def draft(self, difficulty: int = None, max_retries: int = 3, verbose: bool = False, category: Optional[str] = None, theme: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Generate and validate a mission draft using OpenAI API.
        
        Args:
            difficulty: Target difficulty (1-5). If None, random.
            max_retries: Maximum retry attempts if validation fails (default: 3)
            verbose: Print validation errors for debugging
            category: Challenge category (e.g., "WEB_SQLI", "CRYPTO_RSA"). If None, random.
            theme: Visual theme (e.g., "CORPORATE", "UNDERGROUND"). If None, random.
            
        Returns:
            Tuple of (success, file_path, mission_data)
        """
        for attempt in range(max_retries):
            try:
                # Generate mission using AI
                mission = self._generate_with_ai(difficulty, category=category, theme=theme)
                
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
            verbose=args.verbose,
            category=args.category,
            theme=args.theme
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

