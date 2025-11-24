"""
SQL Injection Challenge - sqli-01
Vulnerable FastAPI application for CTF training
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import sqlite3
import secrets
import os

app = FastAPI(title="Secret Admin Panel")

# SQLite in-memory database
DB_PATH = ":memory:"
conn = None

# Flag (環境変数から取得、デフォルト値あり)
FLAG = os.getenv("CTF_FLAG", "SolCTF{y0u_f0und_7h3_sql_m4s73r_k3y}")


def init_db():
    """データベースを初期化"""
    global conn
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # usersテーブル作成
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # secretsテーブル作成
    cursor.execute("""
        CREATE TABLE secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
    """)
    
    # adminユーザーを追加（ランダムな激ムズパスワード）
    admin_password = secrets.token_urlsafe(32)
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("admin", admin_password)
    )
    
    # Flagをsecretsテーブルに追加
    cursor.execute(
        "INSERT INTO secrets (key_name, value) VALUES (?, ?)",
        ("flag", FLAG)
    )
    
    conn.commit()
    print(f"[INFO] Database initialized. Admin password: {admin_password}")
    print(f"[INFO] Flag stored in secrets table: {FLAG}")


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時にDBを初期化"""
    init_db()


@app.get("/", response_class=HTMLResponse)
async def login_page():
    """ログイン画面を表示"""
    html = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>極秘管理パネル</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Courier New', monospace;
                background: #0a0a0a;
                color: #e4e4e7;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: #18181b;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 40px;
                max-width: 500px;
                width: 100%;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .header h1 {
                color: #10b981;
                font-size: 24px;
                margin-bottom: 10px;
                text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
            }
            .header p {
                color: #71717a;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            .warning {
                background: #7f1d1d;
                border: 1px solid #991b1b;
                color: #fca5a5;
                padding: 12px;
                border-radius: 4px;
                margin-bottom: 20px;
                font-size: 12px;
                text-align: center;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                color: #a1a1aa;
                font-size: 12px;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            input[type="text"],
            input[type="password"] {
                width: 100%;
                padding: 12px;
                background: #0a0a0a;
                border: 1px solid #27272a;
                border-radius: 4px;
                color: #e4e4e7;
                font-family: 'Courier New', monospace;
                font-size: 14px;
            }
            input[type="text"]:focus,
            input[type="password"]:focus {
                outline: none;
                border-color: #10b981;
                box-shadow: 0 0 5px rgba(16, 185, 129, 0.3);
            }
            button {
                width: 100%;
                padding: 12px;
                background: #10b981;
                color: #0a0a0a;
                border: none;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
                text-transform: uppercase;
                letter-spacing: 1px;
                transition: background 0.3s;
            }
            button:hover {
                background: #059669;
            }
            .error {
                background: #7f1d1d;
                border: 1px solid #991b1b;
                color: #fca5a5;
                padding: 12px;
                border-radius: 4px;
                margin-top: 20px;
                font-size: 12px;
            }
            .success {
                background: #064e3b;
                border: 1px solid #065f46;
                color: #6ee7b7;
                padding: 20px;
                border-radius: 4px;
                margin-top: 20px;
            }
            .success h2 {
                color: #10b981;
                margin-bottom: 15px;
                font-size: 18px;
            }
            .flag {
                background: #0a0a0a;
                border: 1px solid #10b981;
                padding: 15px;
                border-radius: 4px;
                margin-top: 15px;
                font-family: 'Courier New', monospace;
                font-size: 16px;
                color: #10b981;
                text-align: center;
                word-break: break-all;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ 極秘管理パネル ⚡</h1>
                <p>Authorized Personnel Only</p>
            </div>
            <div class="warning">
                ⚠️ 不正アクセスは厳重に処罰されます
            </div>
            <form method="POST" action="/login">
                <div class="form-group">
                    <label for="username">ユーザー名</label>
                    <input type="text" id="username" name="username" required autofocus>
                </div>
                <div class="form-group">
                    <label for="password">パスワード</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">認証</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    ログイン処理（SQLインジェクション脆弱性あり）
    
    ⚠️ 警告: このコードは意図的に脆弱性を含んでいます。
    本番環境では絶対に使用しないでください。
    """
    global conn
    
    try:
        cursor = conn.cursor()
        
        # ⚠️ 脆弱性: f-stringでSQLを直接組み立て（プレースホルダ不使用）
        # これによりSQLインジェクションが可能
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        
        print(f"[DEBUG] Executing query: {query}")
        cursor.execute(query)
        user = cursor.fetchone()
        
        if user:
            # ログイン成功: Flagを取得して表示
            cursor.execute("SELECT value FROM secrets WHERE key_name = 'flag'")
            flag_result = cursor.fetchone()
            flag_value = flag_result[0] if flag_result else "Flag not found"
            
            success_html = f"""
            <!DOCTYPE html>
            <html lang="ja">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>認証成功</title>
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: 'Courier New', monospace;
                        background: #0a0a0a;
                        color: #e4e4e7;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 20px;
                    }}
                    .container {{
                        background: #18181b;
                        border: 1px solid #27272a;
                        border-radius: 8px;
                        padding: 40px;
                        max-width: 600px;
                        width: 100%;
                        box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
                    }}
                    .success {{
                        background: #064e3b;
                        border: 1px solid #065f46;
                        color: #6ee7b7;
                        padding: 20px;
                        border-radius: 4px;
                    }}
                    .success h2 {{
                        color: #10b981;
                        margin-bottom: 15px;
                        font-size: 18px;
                    }}
                    .flag {{
                        background: #0a0a0a;
                        border: 1px solid #10b981;
                        padding: 15px;
                        border-radius: 4px;
                        margin-top: 15px;
                        font-family: 'Courier New', monospace;
                        font-size: 16px;
                        color: #10b981;
                        text-align: center;
                        word-break: break-all;
                    }}
                    .info {{
                        color: #71717a;
                        font-size: 12px;
                        margin-top: 20px;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success">
                        <h2>✓ 認証成功</h2>
                        <p>ようこそ、管理者様。</p>
                        <div class="flag">
                            🏴 FLAG: {flag_value}
                        </div>
                        <div class="info">
                            <a href="/" style="color: #10b981;">← ログアウト</a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=success_html)
        else:
            # ログイン失敗
            error_html = f"""
            <!DOCTYPE html>
            <html lang="ja">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>認証失敗</title>
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: 'Courier New', monospace;
                        background: #0a0a0a;
                        color: #e4e4e7;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 20px;
                    }}
                    .container {{
                        background: #18181b;
                        border: 1px solid #27272a;
                        border-radius: 8px;
                        padding: 40px;
                        max-width: 500px;
                        width: 100%;
                        box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
                    }}
                    .error {{
                        background: #7f1d1d;
                        border: 1px solid #991b1b;
                        color: #fca5a5;
                        padding: 20px;
                        border-radius: 4px;
                        text-align: center;
                    }}
                    .error h2 {{
                        color: #f87171;
                        margin-bottom: 10px;
                    }}
                    .info {{
                        color: #71717a;
                        font-size: 12px;
                        margin-top: 20px;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error">
                        <h2>✗ 認証失敗</h2>
                        <p>ユーザー名またはパスワードが正しくありません。</p>
                        <div class="info">
                            <a href="/" style="color: #10b981;">← 再試行</a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=error_html)
    
    except Exception as e:
        # エラー発生時
        error_html = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <title>エラー</title>
            <style>
                body {{
                    font-family: 'Courier New', monospace;
                    background: #0a0a0a;
                    color: #fca5a5;
                    padding: 40px;
                }}
                .error {{
                    background: #7f1d1d;
                    border: 1px solid #991b1b;
                    padding: 20px;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2>エラーが発生しました</h2>
                <p>{str(e)}</p>
                <a href="/" style="color: #10b981;">← 戻る</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

