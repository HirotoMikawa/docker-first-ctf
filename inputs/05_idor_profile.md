# Employee Profile System: IDOR (Insecure Direct Object Reference)

## シナリオ

あなたは、Silverhand Industries のセキュリティ監査チームとして、従業員プロフィールシステムの認可機能を検証している。

**ターゲット**: 従業員情報管理システム  
**目的**: IDOR脆弱性を利用し、他のユーザー（特に管理者）の情報にアクセスせよ  
**インテル**: このシステムは `/profile?id=` パラメータでユーザーを識別しているが、適切な認可チェックが行われていない可能性がある。あなたの任務は、自分以外のユーザー（管理者ID=1）のプロフィールにアクセスし、そこに含まれる機密フラグを入手することだ。

**ミッション**: パラメータ改変により、管理者のプロフィールにアクセスせよ。

---

## 技術的背景: IDOR（Insecure Direct Object Reference）とは

### 概要

**IDOR** は、アプリケーションがオブジェクト（ユーザー、ファイル、データ等）への参照（ID）を直接URL等で公開しており、かつ適切な認可チェックを行っていない場合に発生する脆弱性です。

### 仕組み

```
通常のアクセス:
  /profile?id=105 → ユーザー105の情報を表示

IDOR攻撃:
  /profile?id=1 → 管理者の情報も表示されてしまう
  /profile?id=2 → 他のユーザーの情報も表示されてしまう
```

**問題点**: 「このIDにアクセスする権限があるか？」をチェックしていない

---

## 脆弱なコードの仕様

### アプリケーション構成

**技術スタック**:
- **言語**: Python 3.11
- **フレームワーク**: Flask 3.0.0
- **データベース**: SQLite
- **認証**: セッション（簡易版）
- **ポート**: 8000

### データベーススキーマ

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    role TEXT,
    bio TEXT
);

INSERT INTO users VALUES
(1, 'admin', 'admin@silverhand.corp', 'Administrator', 'SolCTF{idor_silverhand_profile_leak}'),
(105, 'employee', 'emp105@silverhand.corp', 'Employee', '普通の従業員です'),
(106, 'guest', 'guest@silverhand.corp', 'Guest', 'ゲストユーザー');
```

### 脆弱なコード実装

```python
from flask import Flask, request, render_template_string, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            role TEXT,
            bio TEXT
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO users VALUES (1, 'admin', 'admin@silverhand.corp', 'Administrator', 'SolCTF{idor_silverhand_profile_leak}')")
    cursor.execute("INSERT OR IGNORE INTO users VALUES (105, 'employee', 'emp105@silverhand.corp', 'Employee', '普通の従業員です')")
    cursor.execute("INSERT OR IGNORE INTO users VALUES (106, 'guest', 'guest@silverhand.corp', 'Guest', 'ゲストユーザー')")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template_string('''
        <h1>SILVERHAND INDUSTRIES</h1>
        <h2>Employee Profile System</h2>
        <ul>
            <li><a href="/login">Login</a></li>
        </ul>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        # 簡易認証（パスワードなし）
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            return f'<p>ログイン成功！ <a href="/profile?id={user[0]}">マイプロフィール</a></p>'
        else:
            return '<p>ユーザーが見つかりません <a href="/login">戻る</a></p>'
    
    return render_template_string('''
        <h1>Login</h1>
        <form method="post">
            <input type="text" name="username" placeholder="employee または guest">
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/profile')
def profile():
    # ❌ 脆弱性: 認可チェックなし
    user_id = request.args.get('id', '')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return render_template_string('''
            <div style="background:#0a0a0a;color:#00aaff;font-family:monospace;padding:20px;">
                <h1>SILVERHAND INDUSTRIES</h1>
                <h2>User Profile</h2>
                <hr>
                <p><b>ID:</b> {{ user[0] }}</p>
                <p><b>Username:</b> {{ user[1] }}</p>
                <p><b>Email:</b> {{ user[2] }}</p>
                <p><b>Role:</b> {{ user[3] }}</p>
                <hr>
                <div style="border:2px solid #ff0080;padding:15px;">
                    <p><b>Bio:</b></p>
                    <pre>{{ user[4] }}</pre>
                </div>
                <p><a href="/">Home</a></p>
            </div>
        ''', user=user)
    else:
        return '<p>User not found</p>'

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=8000)
```

---

## 攻略手順

### ステップ1: ログイン

1. `http://{{CONTAINER_HOST}}/login` にアクセス
2. ユーザー名: `employee` でログイン
3. マイプロフィールへのリンクが表示: `/profile?id=105`

### ステップ2: 自分のプロフィール確認

URL: `http://{{CONTAINER_HOST}}/profile?id=105`

表示内容:
- ID: 105
- Username: employee
- Role: Employee
- Bio: 普通の従業員です

### ステップ3: パラメータ改変

**ID=1に変更**:

URL: `http://{{CONTAINER_HOST}}/profile?id=1`

### ステップ4: フラグ取得

**結果**:
- ID: 1
- Username: admin
- Role: Administrator
- **Bio**: `SolCTF{idor_silverhand_profile_leak}`

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
Silverhand Industries の従業員情報管理システムが、内部監査の対象となった。このシステムは各従業員が自分のプロフィールを閲覧できる機能を持つが、URLパラメータによる認可チェックが不十分であるとの指摘がある。あなたの任務は、IDOR脆弱性を利用して管理者（ID=1）のプロフィールにアクセスし、そこに含まれる機密フラグを入手することだ。
```

## タグ

- Web
- IDOR
- Authorization
- Beginner
- Access Control

## 対策

```python
# ✅ セキュアな実装
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    requested_id = request.args.get('id', '')
    current_user_id = session['user_id']
    
    # 認可チェック: 自分のIDのみアクセス可能
    if str(requested_id) != str(current_user_id):
        return "Access Denied: 他のユーザーの情報にはアクセスできません"
    
    # ... プロフィール表示
```

