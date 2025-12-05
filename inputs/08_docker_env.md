# Container Debug Panel: Environment Variable Exposure

## シナリオ

あなたは、Trauma Team Internationalのインフラセキュリティチームとして、コンテナ化されたアプリケーションのセキュリティ診断を実施している。

**ターゲット**: Dockerコンテナで動作するWebアプリケーション  
**目的**: 環境変数に含まれる機密情報を取得せよ  
**インテル**: このアプリケーションはデバッグ機能が有効になっており、環境変数が漏洩する可能性がある。Dockerコンテナでは、機密情報（APIキー、データベースパスワード、フラグ等）を環境変数として渡すことが一般的だが、適切に保護されていない場合、攻撃者に取得されてしまう。あなたの任務は、デバッグエンドポイントから環境変数`FLAG`を読み取り、機密フラグを入手することだ。

**ミッション**: 環境変数の漏洩経路を発見し、フラグを取得せよ。

---

## 技術的背景: Docker環境変数の脆弱性

### Dockerの環境変数

Dockerコンテナでは、機密情報を環境変数として渡すことが一般的です:

```dockerfile
ENV FLAG="SolCTF{secret_flag}"
ENV API_KEY="abc123xyz"
ENV DB_PASSWORD="password123"
```

コンテナ内のアプリケーションは、以下で環境変数にアクセスできます:

```python
import os
flag = os.environ.get('FLAG')
api_key = os.getenv('API_KEY')
```

### 脆弱性が発生するケース

1. **デバッグエンドポイントの露出**:
   ```python
   @app.route('/debug')
   def debug():
       return str(os.environ)  # 全環境変数を表示
   ```

2. **エラーメッセージに含まれる**:
   ```python
   return f"Error: {os.environ}"
   ```

3. **ログファイルに記録**:
   ```python
   logger.debug(f"Env: {os.environ}")
   ```

---

## 脆弱なコードの仕様

### アプリケーション構成

**技術スタック**:
- **言語**: Python 3.11
- **フレームワーク**: Flask 3.0.0
- **デプロイ**: Docker
- **ポート**: 8000

### 脆弱なコード実装

```python
from flask import Flask, request, render_template_string
import os
import sys

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>Docker環境変数 - デバッグ情報</title>
            <style>
                body {
                    background: #0f0f0f;
                    color: #ff6600;
                    font-family: monospace;
                    padding: 20px;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    border: 2px solid #ff6600;
                    padding: 20px;
                    border-radius: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>TRAUMA TEAM INT'L</h1>
                <h2>Application Status Monitor</h2>
                <h3>[DEVELOPMENT BUILD]</h3>
                <hr>
                <p>Application is running...</p>
                <ul>
                    <li><a href="/health" style="color:#0f0;">Health Check</a></li>
                    <li><a href="/info" style="color:#0f0;">System Info</a></li>
                </ul>
                <hr>
                <p style="color:#666;">Debug features enabled</p>
            </div>
        </body>
        </html>
    ''')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "version": "1.0.0"})

@app.route('/info')
def info():
    # システム情報を表示
    info_data = {
        "python_version": sys.version,
        "platform": sys.platform,
        "path": sys.path[:3]
    }
    
    return render_template_string('''
        <h1>System Information</h1>
        <pre>{{ info }}</pre>
        <p>その他のエンドポイント: <a href="/debug">/debug</a> (内部用)</p>
        <a href="/">戻る</a>
    ''', info=info_data)

@app.route('/debug')
def debug():
    # ❌ 脆弱性: 環境変数を全て表示してしまう
    env_vars = dict(os.environ)
    
    return render_template_string('''
        <html>
        <head>
            <title>Debug Panel</title>
            <style>
                body {
                    background: #000;
                    color: #0f0;
                    font-family: monospace;
                    padding: 20px;
                }
                pre {
                    background: #1a1a1a;
                    padding: 15px;
                    border: 1px solid #0f0;
                    overflow-x: auto;
                }
                .warning {
                    color: #f00;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <h1>DEBUG PANEL</h1>
            <p class="warning">⚠️ WARNING: Internal use only</p>
            <hr>
            <h2>Environment Variables:</h2>
            <pre>{{ env }}</pre>
            <a href="/">戻る</a>
        </body>
        </html>
    ''', env=env_vars)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)  # debug=True も脆弱性
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

RUN useradd -m -u 1000 ctfuser

# 環境変数としてフラグを設定（重要！）
ENV FLAG="SolCTF{docker_env_var_leakage}"

WORKDIR /home/ctfuser

COPY app.py requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

USER ctfuser

EXPOSE 8000

CMD ["python", "app.py"]
```

---

## 攻略手順

### ステップ1: 偵察

1. `http://{{CONTAINER_HOST}}/` にアクセス
2. 「Debug features enabled」の表示を確認
3. エンドポイントを確認

### ステップ2: 公開エンドポイントを試す

`/health` → システム状態  
`/info` → システム情報

### ステップ3: デバッグエンドポイントを発見

`/info` ページに「その他のエンドポイント: `/debug`」というヒントがある

### ステップ4: /debug にアクセス

URL: `http://{{CONTAINER_HOST}}/debug`

**結果**: すべての環境変数が表示される

```
{
  'FLAG': 'SolCTF{docker_env_var_leakage}',
  'PATH': '/usr/local/bin:...',
  'PYTHON_VERSION': '3.11.0',
  ...
}
```

### ステップ5: フラグをコピー

`FLAG` の値をコピーして提出。

---

## 難易度

```json
{
  "difficulty": 2,
  "difficulty_factors": {
    "tech": 1,
    "read": 2,
    "explore": 3
  }
}
```

---

## Story Hook

```
Trauma Team International のコンテナ化されたアプリケーションが、セキュリティレビューの対象となった。このアプリケーションは開発ビルドであり、デバッグ機能が有効になっている。Docker環境変数に機密情報が含まれている可能性があり、デバッグエンドポイントから漏洩する危険性がある。あなたの任務は、これらのエンドポイントを探索し、環境変数に含まれる機密フラグを入手することだ。
```

## タグ

- Web
- Docker
- Environment Variables
- Information Disclosure
- Beginner
- Misconfiguration

## 対策

```python
# ✅ セキュアな実装

# 1. デバッグエンドポイントを削除
# /debug エンドポイントは本番環境では無効にする

# 2. debug=False
if __name__ == '__main__':
    app.run(debug=False, ...)

# 3. 環境変数を選択的に表示
SAFE_VARS = ['PYTHON_VERSION', 'PATH']
safe_env = {k: v for k, v in os.environ.items() if k in SAFE_VARS}

# 4. 機密情報は環境変数ではなく、Secretsを使用
# Docker Secrets, Kubernetes Secrets, AWS Secrets Manager等
```

