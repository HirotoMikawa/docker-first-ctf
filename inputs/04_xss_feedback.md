# Customer Feedback System: Stored XSS Attack

## シナリオ

あなたは、Phantom Protocol Security Teamの一員として、顧客フィードバックシステムのセキュリティテストを実施している。

**ターゲット**: 顧客フィードバック投稿システム  
**目的**: Stored XSS脆弱性を利用し、管理者セッションを奪取せよ  
**インテル**: このシステムはユーザーの投稿を管理者が閲覧する仕組みだが、入力値のサニタイズが行われていない。XSS攻撃により、管理者のCookieやセッション情報を取得できる可能性がある。あなたの任務は、XSSペイロードを投稿し、システム内に隠された機密フラグを入手することだ。

**ミッション**: Stored XSSを実行し、フラグを取得せよ。

---

## 技術的背景: XSS（Cross-Site Scripting）とは

### 概要

**XSS（Cross-Site Scripting）** は、Webアプリケーションがユーザー入力をエスケープせずにHTMLとして出力することで、悪意のあるJavaScriptを他のユーザーのブラウザで実行させる脆弱性です。

### XSSの種類

1. **Reflected XSS**: URLパラメータ等から即座に反映
2. **Stored XSS**: データベースに保存され、他のユーザーが閲覧時に実行
3. **DOM-based XSS**: JavaScriptによるDOM操作で発生

この問題は **Stored XSS** です。

### 仕組み

```
ユーザー投稿: <script>alert(document.cookie)</script>
       ↓
データベースに保存
       ↓
管理者が閲覧
       ↓
ブラウザがJavaScriptとして実行
       ↓
管理者のCookie等が盗まれる
```

---

## 脆弱なコードの仕様

### アプリケーション構成

**技術スタック**:
- **言語**: Python 3.11
- **フレームワーク**: Flask 3.0.0
- **データベース**: SQLite（簡易版）またはメモリ内リスト
- **ポート**: 8000

### 脆弱なコード実装

```python
from flask import Flask, request, render_template_string, session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 投稿を保存（簡易版）
feedbacks = []

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>XSS - フィードバックシステム</title>
            <style>
                body {
                    background: #0a0a0a;
                    color: #00aaff;
                    font-family: monospace;
                    padding: 20px;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    border: 2px solid #00aaff;
                    padding: 20px;
                    border-radius: 10px;
                }
                textarea {
                    width: 100%;
                    height: 100px;
                    background: #1a1a1a;
                    color: #00aaff;
                    border: 1px solid #00aaff;
                    font-family: monospace;
                    padding: 10px;
                }
                input[type="submit"] {
                    background: #00aaff;
                    color: #0a0a0a;
                    border: none;
                    padding: 10px 20px;
                    cursor: pointer;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>PHANTOM PROTOCOL</h1>
                <h2>Customer Feedback System</h2>
                <h3>[PUBLIC ACCESS]</h3>
                <hr>
                <form method="post" action="/submit">
                    <label>Your Feedback:</label><br>
                    <textarea name="feedback" placeholder="ご意見をお聞かせください..."></textarea><br><br>
                    <input type="submit" value="Submit Feedback">
                </form>
                <hr>
                <p style="color: #666;">管理者がフィードバックを確認します。</p>
                <p><a href="/admin" style="color: #00aaff;">管理者ページ（内部用）</a></p>
            </div>
        </body>
        </html>
    ''')

@app.route('/submit', methods=['POST'])
def submit():
    feedback = request.form['feedback']
    feedbacks.append(feedback)
    
    return render_template_string('''
        <h1>Thank you!</h1>
        <p>フィードバックを受け付けました。</p>
        <p>管理者が確認次第、対応いたします。</p>
        <a href="/">戻る</a>
    ''')

@app.route('/admin')
def admin():
    # ❌ 脆弱性: XSS保護なしで投稿を表示
    flag = os.environ.get('FLAG', 'SolCTF{xss_phantom_protocol}')
    
    feedback_html = ""
    for i, fb in enumerate(feedbacks):
        # ❌ autoescape=False または safe フィルタなしで直接表示
        feedback_html += f"<div style='border:1px solid #666; padding:10px; margin:10px 0;'><b>投稿 #{i+1}:</b><br>{fb}</div>"
    
    return render_template_string(f'''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>管理者ページ</title>
            <style>
                body {{
                    background: #0a0a0a;
                    color: #ff0080;
                    font-family: monospace;
                    padding: 20px;
                }}
                .admin-container {{
                    border: 2px solid #ff0080;
                    padding: 20px;
                    max-width: 900px;
                    margin: 0 auto;
                }}
                .flag {{
                    background: #1a1a1a;
                    border: 2px solid #ff0080;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="admin-container">
                <h1>PHANTOM PROTOCOL</h1>
                <h2>管理者ダッシュボード</h2>
                <hr>
                <div class="flag">
                    <h3>[CLASSIFIED]</h3>
                    <p>Admin Flag: <code>{flag}</code></p>
                </div>
                <h3>受信フィードバック:</h3>
                {feedback_html}
                <a href="/">戻る</a>
            </div>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
```

---

## 攻略手順

### ステップ1: 偵察

1. `http://{{CONTAINER_HOST}}/` にアクセス
2. フィードバックフォームを確認
3. 「管理者ページ」のリンクをクリック

### ステップ2: 管理者ページの確認

1. `/admin` にアクセス
2. フラグが表示されている！
3. **しかし、これは管理者のみが見られるページ**

### ステップ3: XSSペイロードの投稿

**基本的なペイロード**:

```html
<script>alert(1)</script>
```

フィードバックフォームに投稿後、`/admin` で確認すると、アラートが表示される（XSS成功）

### ステップ4: フラグ取得

**方法1: 直接表示**

```html
<script>
alert(document.querySelector('.flag code').textContent);
</script>
```

**方法2: コンソールに出力**

```html
<script>
console.log(document.querySelector('.flag code').textContent);
</script>
```

投稿後、`/admin` にアクセスし、ブラウザのコンソール（F12）を開いてフラグを確認。

**方法3: 簡易版（この問題の正解）**

単純に `/admin` ページに直接アクセスするだけでフラグが見える（認証なし）。

または、XSSで以下を実行:
```html
<img src=x onerror="alert(this.parentElement.querySelector('.flag code').textContent)">
```

---

## 難易度

```json
{
  "difficulty": 2,
  "difficulty_factors": {
    "tech": 2,
    "read": 2,
    "explore": 2
  }
}
```

---

## Story Hook

```
Phantom Protocolの顧客フィードバックシステムがセキュリティ監査の対象となった。このシステムは顧客からの意見を収集し、管理者が閲覧する仕組みだが、入力値のエスケープ処理が不十分であるとの報告がある。あなたの任務は、Stored XSS攻撃により管理者ページに保存されたフラグを入手することだ。
```

## タグ

- Web
- XSS
- Stored XSS
- Beginner
- JavaScript

## 対策

```python
# ✅ セキュアな実装
from markupsafe import escape

feedback_html = ""
for fb in feedbacks:
    feedback_html += f"<div>{escape(fb)}</div>"

# または、Jinjaテンプレートの自動エスケープを使用
```

