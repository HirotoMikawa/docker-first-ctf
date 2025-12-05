# Project Sol: 問題生成用ソーステキスト (Source Texts)

このディレクトリには、AI問題生成エンジンの「種データ（Source Text）」が保存されています。

---

## 📋 概要

### 目的

高品質なCTF問題を生成するために、技術的に正確で教育的な参考資料を提供します。

### 使い方

```bash
# ソーステキストを指定して問題を生成
python tools/cli.py auto-add --source inputs/sqli_basic.md --no-deploy
```

---

## 📚 利用可能なソーステキスト

### 全10問 - Phase 1初期コンテンツセット

| # | ファイル | カテゴリ | 難易度 | タイトル | 説明 |
|---|---------|----------|--------|----------|------|
| 01 | `sqli_basic.md` | SQLi | 1 | SQLインジェクション - ログインバイパス | Arasaka Corp従業員ポータル |
| 02 | `02_rce_ping.md` | RCE | 2 | OSコマンドインジェクション - Ping | NetWatch監視ツール |
| 03 | `03_traversal_file.md` | Path Traversal | 2 | パストラバーサル - ファイル閲覧 | Militech社内ドキュメント |
| 04 | `04_xss_feedback.md` | XSS | 2 | XSS - フィードバックシステム | Phantom Protocolカスタマーサポート |
| 05 | `05_idor_profile.md` | IDOR | 2 | IDOR - プロフィール閲覧 | Silverhand従業員情報システム |
| 06 | `06_ssrf_proxy.md` | SSRF | 3 | SSRF - URLプレビュー | Biotechnica URLプレビューサービス |
| 07 | `07_jwt_none.md` | JWT | 3 | JWT認証 - None Algorithm | Night City API認証システム |
| 08 | `08_docker_env.md` | Misc | 2 | Docker環境変数 - デバッグ情報 | Trauma Team監視システム |
| 09 | `09_crypto_rsa.md` | Crypto | 3 | RSA暗号 - 弱い鍵 | Kang Tao暗号化通信 |
| 10 | `10_logic_shop.md` | Logic | 3 | ロジックエラー - ショップ | Afterlife闇市マーケット |

### 難易度分布

- **難易度1**: 1問（10%）
- **難易度2**: 5問（50%）
- **難易度3**: 4問（40%）

**合計**: 10問

### カテゴリ分布

- **Web**: 8問（SQLi, RCE, Path Traversal, XSS, IDOR, SSRF, JWT, Logic）
- **Misc**: 1問（Docker Env）
- **Crypto**: 1問（RSA）

---

## 🔧 ソーステキストの作成方法

### 基本構成

各ソーステキストは、以下のセクションを含むべきです：

1. **タイトルとシナリオ**
   - Problem Solのストーリー性に合致
   - Cyberpunk/Corporateテーマ

2. **技術的背景**
   - 脆弱性の説明
   - 仕組みの解説

3. **脆弱なコードの仕様**
   - 具体的な実装例
   - 必須要件と禁止事項

4. **攻略手順**
   - ステップバイステップ
   - 実際のペイロード例

5. **対策**
   - セキュアな実装例
   - ベストプラクティス

### テンプレート

```markdown
# [Problem Title]: [Vulnerability Type] Basics

## シナリオ
（ストーリー設定）

## 技術的背景
（脆弱性の説明）

## 脆弱なコードの仕様
（実装要件）

## 攻略手順
（解法）

## 対策
（セキュアな実装例）

## 難易度設定
（推奨値）
```

---

## 💡 ソーステキストの活用方法

### パターン1: 単一ソースから問題生成

```bash
# 1. ソーステキストを準備
# inputs/sqli_basic.md を使用

# 2. 問題生成
python tools/cli.py auto-add --source inputs/sqli_basic.md --no-deploy

# 3. レビュー・調整
./tools/check_quality.sh challenges/drafts/SOL-MSN-XXXX.json

# 4. Cursorで手直し（必要に応じて）
code challenges/drafts/SOL-MSN-XXXX.json

# 5. デプロイ
python tools/cli.py deploy challenges/drafts/SOL-MSN-XXXX.json
```

### パターン2: 複数ソースから連続生成

```bash
# 初期5問を参考資料ベースで生成
for source in inputs/*.md; do
  echo "=== Generating from: $source ==="
  python tools/cli.py auto-add --source "$source" --no-deploy
  sleep 10
done
```

### パターン3: 外部記事の活用

```bash
# 1. Webから技術記事を取得
# 例: Qiita、Zenn、ブログ記事等

# 2. テキストファイルとして保存
cat > inputs/custom_vulnerability.txt << 'EOF'
（記事の内容をコピー&ペースト）
EOF

# 3. 問題生成
python tools/cli.py auto-add --source inputs/custom_vulnerability.txt --no-deploy
```

---

## 🎯 Cursorによる手直しの例

生成された問題は、JSONファイルを編集することで自由にカスタマイズできます。

### 例1: デザインの改善

**生成されたHTML**:
```html
<h1>Login</h1>
<form>...</form>
```

**Cursorへの指示**:
```
「ログイン画面のデザインを改善して。
背景を#0a0a0aに、テキストを#00ff00に、
CSSでグラデーションボーダーを追加して。
Arasaka Corpのロゴっぽいアスキーアートも入れて。」
```

**編集箇所**: `files["app.py"]` 内のHTML/CSS

---

### 例2: 解説の詳細化

**生成されたWriteup**:
```markdown
## 解法
1. SQLインジェクションを実行
2. フラグを取得
```

**Cursorへの指示**:
```
「解説をもっと詳しくして。
- なぜ ' OR '1'='1 が有効なのか
- SQL文の構造変化を図解
- 初心者向けに噛み砕いて説明
- スクリーンショット用のコマンド例も追加」
```

**編集箇所**: `writeup` フィールド

---

### 例3: 脆弱性の調整

**生成されたコード**:
```python
# もし shell=False になっていたら
subprocess.run(['ping', target], shell=False, ...)
```

**Cursorへの指示**:
```
「shell=False を shell=True に変更して。
コマンドを f"ping -c 4 {target}" の形式にして。
コマンドインジェクションが確実に動作するように。」
```

**編集箇所**: `files["app.py"]` 内のコード

---

### 例4: 難易度の微調整

**生成された難易度**: 1

**実際にテストした結果**: 難易度2が適切

**Cursorへの指示**:
```
「difficulty を 1 から 2 に変更。
difficulty_factors も以下に変更：
tech=2, read=2, explore=2」
```

**編集箇所**: `difficulty` と `difficulty_factors`

---

## 📊 ソーステキストの品質基準

### 良いソーステキストの条件

✅ **技術的に正確**
- 脆弱性の説明が正しい
- コード例が実際に動作する
- セキュアな実装例も提示

✅ **教育的**
- 初心者にも理解できる説明
- ステップバイステップの手順
- 学習目標が明確

✅ **Project Sol のテーマに合致**
- Cyberpunk/Corporate/Combat トーン
- ストーリー性のあるシナリオ
- 禁止用語（Great, Good luck等）を含まない

✅ **AI生成に適した構造**
- 必須要件が明確
- 禁止事項が明示
- 期待される成果物が具体的

---

## 🔄 ワークフロー

### 推奨: ハイブリッドアプローチ

```
┌────────────────────────────────────┐
│  1. ソーステキスト作成              │
│     inputs/*.md                    │
│     （人間が執筆または収集）        │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│  2. AI生成（Draft）                │
│     python tools/cli.py auto-add   │
│     --source inputs/*.md           │
│     --no-deploy                    │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│  3. 自動品質チェック               │
│     ./tools/check_quality.sh       │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│  4. 手動レビュー・テスト           │
│     実際に問題を解く               │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│  5. Cursorで手直し（オプション）   │
│     デザイン、解説、コード調整     │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│  6. 再ビルド・テスト               │
│     python tools/cli.py build      │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│  7. デプロイ                       │
│     python tools/cli.py deploy     │
└────────────────────────────────────┘
```

---

## 📝 今後の追加予定

### 優先度 High

- [ ] `path_traversal_basic.md` - ディレクトリトラバーサル
- [ ] `idor_basic.md` - IDOR（認可バイパス）

### 優先度 Medium

- [ ] `ssrf_basic.md` - SSRF（内部リソースアクセス）
- [ ] `xxe_basic.md` - XXE（XML外部エンティティ）

### 優先度 Low

- [ ] `sqli_advanced.md` - Blind SQLi、UNION攻撃
- [ ] `rce_deserialization.md` - Pickle、オブジェクト注入
- [ ] `privilege_escalation.md` - 権限昇格

---

## 🎓 学んだベストプラクティス

### 1. 具体性が重要

**❌ 悪い例**:
```
SQLインジェクションの問題を作ってください
```

**✅ 良い例**:
```markdown
# 脆弱なコード実装
query = f"SELECT * FROM users WHERE username='{username}'"
cursor.execute(query)
```

### 2. 禁止事項の明示

**必須**:
- `/flag` エンドポイント禁止
- `shell=False` 禁止（RCE問題）
- Prepared Statement禁止（SQLi問題）

### 3. UIデザインの指定

**効果的**:
- 色指定（`#0a0a0a`）
- スタイル指定（Cyberpunk）
- 具体的なHTML例

---

## 🚀 クイックスタート

### 初めて使う場合

```bash
# 1. SQLインジェクション問題を生成
cd ~/my_ctf_product
source venv/bin/activate
export $(cat .env | xargs)

python tools/cli.py auto-add \
  --source inputs/sqli_basic.md \
  --no-deploy \
  --difficulty 1

# 2. 品質チェック
./tools/check_quality.sh challenges/drafts/SOL-MSN-XXXX.json

# 3. テスト
# （実際に問題を解いてみる）

# 4. デプロイ
python tools/cli.py deploy challenges/drafts/SOL-MSN-XXXX.json
```

---

**Last Updated**: 2025-12-04

