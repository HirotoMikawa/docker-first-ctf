# Project Sol: 動作確認ガイド

## 📋 前提条件の確認

### 1. 環境変数の設定

`.env`ファイルに以下が設定されているか確認してください：

```bash
GEMINI_API_KEY=あなたのAPIキー
USE_GEMINI=true  # オプション（デフォルトでtrue）
```

### 2. 依存関係のインストール

```bash
pip install -r requirements-core.txt
```

---

## 🧪 動作確認手順

### Step 1: テスト用ソースファイルの準備

```bash
# 入力ディレクトリを作成
mkdir -p inputs

# テスト用ソースファイルを作成
cat > inputs/os_command_injection.txt << "EOL"
OS Command Injection（OSコマンドインジェクション）は、
Webアプリケーションの脆弱性の一つです。
攻撃者が悪意のあるOSコマンドを入力フィールドに注入することで、
サーバー上で任意のコマンドが実行される可能性があります。

対策としては、シェル実行を避けるか、
ホワイトリスト方式で許可されたコマンドのみを実行することが推奨されます。
EOL
```

### Step 2: RAGモードで問題を生成

```bash
python tools/cli.py auto-add --source inputs/os_command_injection.txt
```

**期待される動作:**
```
[INFO] Starting auto-generation sequence...

[1/8] Generating draft mission JSON with Gemini API...
[INFO] Loaded source text from: inputs/os_command_injection.txt (XX characters)
[1/8] ✓ Draft generated: challenges/drafts/SOL-MSN-XXXX.json
      Mission ID: SOL-MSN-XXXX

[2/8] Validating Dockerfile...

[3/8] Building Docker image...
[INFO] Using AI-generated files from JSON
[INFO] Created file: app.py
[INFO] Created file: Dockerfile
[INFO] Created file: requirements.txt
[3/8] ✓ Docker Image Built

[4/8] Starting test container and verifying solvability...
[4/8] ✓ Test container started
      Container ID: xxxxxxxxxxxx
      Container URL: http://localhost:XXXXX

...（以下、テスト・デプロイの流れ）
```

### Step 3: 生成されたファイルの確認

```bash
# 最新のJSONファイルを確認
ls -lt challenges/drafts/ | head -5

# JSONファイルの内容を確認（filesオブジェクトが含まれているか）
cat challenges/drafts/SOL-MSN-*.json | jq '.files' | head -30

# Dockerfileにflag.txtが作成されているか確認
cat challenges/drafts/SOL-MSN-*.json | jq -r '.files.Dockerfile' | grep -i flag
```

**確認ポイント:**
- ✅ `files`オブジェクトに`app.py`、`Dockerfile`、`requirements.txt`が含まれている
- ✅ `Dockerfile`に`RUN echo ... > /flag.txt`または`RUN echo ... > /home/ctfuser/flag.txt`が含まれている
- ✅ `app.py`で参照しているファイルパスと`Dockerfile`のパスが一致している

### Step 4: コンテナ内でファイルの存在確認

```bash
# コンテナIDを取得
docker ps

# コンテナに入る
docker exec -it <container_id> /bin/sh

# フラグファイルの存在を確認
# RCE問題の場合:
cat /home/ctfuser/flag.txt

# Web問題（SQLi等）の場合:
cat /flag.txt
env | grep FLAG

# その他のファイルも確認（app.pyで参照しているファイル）
ls -la /home/ctfuser/
ls -la /
```

**確認ポイント:**
- ✅ `app.py`で参照しているファイルが実際に存在する
- ✅ フラグファイルが正しいパスに存在する
- ✅ ファイルの権限が適切（`ctfuser`が読み取り可能）

---

## 🔍 トラブルシューティング

### エラー: `GEMINI_API_KEY environment variable is required`

**原因:** APIキーが設定されていない

**対処:**
```bash
# .envファイルにAPIキーを設定
echo "GEMINI_API_KEY=あなたのAPIキー" >> .env
```

### エラー: `File not found: inputs/os_command_injection.txt`

**原因:** ソースファイルが存在しない

**対処:**
```bash
# ファイルが存在するか確認
ls -la inputs/

# 存在しない場合は作成
mkdir -p inputs
# （上記のStep 1を実行）
```

### エラー: Docker build failed

**原因:** Dockerfileに問題がある可能性

**対処:**
```bash
# 生成されたDockerfileを確認
cat challenges/drafts/SOL-MSN-*.json | jq -r '.files.Dockerfile'

# 手動でビルドしてエラーを確認
docker build -t test-image -f - <(cat challenges/drafts/SOL-MSN-*.json | jq -r '.files.Dockerfile')
```

### コンテナ内でファイルが見つからない

**原因:** FILE PERSISTENCE RULEが正しく適用されていない可能性

**対処:**
1. 生成されたJSONの`files.Dockerfile`を確認
2. `app.py`で参照しているファイルパスを確認
3. `Dockerfile`にそのファイルを作成する`RUN`コマンドがあるか確認
4. なければ、`tools/generation/drafter.py`のSystem Promptを再確認

---

## ✅ 成功の確認

以下のすべてが確認できれば成功です：

- [ ] ソーステキストが正しく読み込まれている
- [ ] 生成されたJSONに`files`オブジェクトが含まれている
- [ ] `Dockerfile`に`flag.txt`が作成されている
- [ ] `app.py`で参照しているファイルが`Dockerfile`で作成されている
- [ ] コンテナ内でファイルが実際に存在する
- [ ] コンテナが正常に起動し、Webアプリが動作する

---

## 📝 次のステップ

動作確認が完了したら：

1. **通常モード（ランダム生成）の確認:**
   ```bash
   python tools/cli.py auto-add
   ```

2. **複数のソースファイルでテスト:**
   ```bash
   # 異なる脆弱性の解説ファイルを作成してテスト
   python tools/cli.py auto-add --source inputs/sql_injection.txt
   python tools/cli.py auto-add --source inputs/xss.txt
   ```

3. **完全版HyRAG-QGへのアップグレード（将来）:**
   - Ingestion Layer（`src/ingest.py`）の実装
   - ChromaDBを使ったベクトル検索の統合
   - LLM-as-a-Judgeの実装

