# Project Sol: Automation Tools (Ver 10.2)

自動化ツール群のドキュメントです。

## 概要

このディレクトリには、Project Sol の自動化ツールが含まれています：

- **CI Validation Tools** (`ci/`): 問題JSONの検証ツール（Phase 3: Auto-Validation）
- **Marketing Tools** (`marketing/`): SNSコンテンツ生成ツール（Phase 1: Content Generation）
- **CLI Tool** (`cli.py`): 統合CLIインターフェース

## 要件

- Python 3.11以上
- OpenAI API key（環境変数 `OPENAI_API_KEY` または `--api-key` オプション、draftコマンド用）
- Supabase認証情報（環境変数 `NEXT_PUBLIC_SUPABASE_URL`/`SUPABASE_URL` と `SUPABASE_SERVICE_KEY`、deployコマンド用）
- 依存パッケージ: `openai`, `python-dotenv`, `supabase`

### インストール

```bash
pip install -r tools/requirements.txt
```

**必要なパッケージ:**
- `openai>=1.0.0` - OpenAI API統合（draftコマンド用）
- `python-dotenv>=1.0.0` - 環境変数読み込み
- `supabase>=2.3.0` - Supabaseクライアント（deployコマンド用）

## 使用方法

### 1. ドラフト生成（Phase 2: Draft Generation）

**前提条件:**
- OpenAI API keyを環境変数 `OPENAI_API_KEY` に設定するか、`--api-key` オプションで指定
- `.env` ファイルに `OPENAI_API_KEY=your-api-key` を記述することも可能

```bash
# ランダムな難易度でドラフト生成（OpenAI API使用）
python3 tools/cli.py draft

# 指定した難易度でドラフト生成
python3 tools/cli.py draft --difficulty 3

# API keyを直接指定
python3 tools/cli.py draft --api-key sk-...

# 出力ディレクトリを指定
python3 tools/cli.py draft --output-dir challenges/drafts

# リトライ回数を指定（デフォルト: 3回）
python3 tools/cli.py draft --max-retries 5

# デバッグモード（検証エラーを表示）
python3 tools/cli.py draft --verbose
```

**生成されるファイル:**
- `challenges/drafts/{mission_id}.json`
- OpenAI API (GPT-4o) を使用して生成
- 自動的に検証を通過する品質のJSONが生成されます
- 検証失敗時は最大3回まで自動リトライ

### 2. データベースへのデプロイ（Phase 3.5: DB Deployment）

**前提条件:**
- Supabase URLとService Keyを環境変数に設定
  - `NEXT_PUBLIC_SUPABASE_URL` または `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
- `.env` ファイルに設定することも可能

```bash
# ドラフトJSONをデータベースにデプロイ
python3 tools/cli.py deploy challenges/drafts/SOL-MSN-XXXX.json

# 検証をスキップしてデプロイ
python3 tools/cli.py deploy challenges/drafts/SOL-MSN-XXXX.json --no-validate

# Supabase認証情報を直接指定
python3 tools/cli.py deploy challenges/drafts/SOL-MSN-XXXX.json \
  --supabase-url https://xxxxx.supabase.co \
  --supabase-service-key sk-...
```

**デプロイされるデータ:**
- `id`: `mission_id` から設定
- `title`: `narrative.story_hook` の最初の文、または `type + difficulty`
- `description`: `narrative.story_hook`
- `difficulty`: `difficulty`
- `points`: `environment.cost_token`
- `image_name`: `environment.image`
- `internal_port`: `environment.internal_port` (デフォルト: 8000)
- `metadata`: JSON全体（jsonb型）
- `status`: `"active"` (即座にプレイ可能にするため)

**マッピング:**
- JSONの `mission_id` → DBの `id` (Primary Key)
- JSONの `narrative.story_hook` → DBの `description`
- JSONの `environment.cost_token` → DBの `points`
- JSON全体 → DBの `metadata` (jsonb型)

### 3. 問題JSONの検証

```bash
python3 tools/cli.py validate challenges/samples/valid_mission.json
```

**検証項目:**
- JSON Schema準拠（PROJECT_MASTER.md）
- 難易度計算式の整合性（DIFFICULTY_SPEC.md）
- Forbidden Wordsチェック（CONTENT_PLAN.md）
- セキュリティ基準チェック（PROJECT_MASTER.md）

**出力:**
- ✓ Validation PASSED: 検証成功
- ✗ Validation FAILED: エラーあり（エラー詳細を表示）

### 4. SNSコンテンツ生成

```bash
# SNS Teaser生成（Intel Mode）
python3 tools/cli.py generate challenges/samples/valid_mission.json sns

# Mission Briefing生成（Combat Mode）
python3 tools/cli.py generate challenges/samples/valid_mission.json briefing
```

**オプション:**
- `base_url`: ミッションリンクのベースURL（SNS形式の場合）

**例:**
```bash
python3 tools/cli.py generate challenges/samples/valid_mission.json sns https://project-sol.example.com
```

## ディレクトリ構造

```
tools/
├── __init__.py
├── cli.py                 # 統合CLIツール
├── README.md             # このファイル
├── requirements.txt      # 依存パッケージ
├── ci/                   # CI検証ツール
│   ├── __init__.py
│   └── validator.py      # 問題JSON検証ロジック
├── generation/           # ドラフト生成ツール
│   ├── __init__.py
│   └── drafter.py        # ドラフト生成ロジック（Phase 2）
├── deploy/               # DBデプロイツール
│   ├── __init__.py
│   └── uploader.py       # データベースデプロイロジック（Phase 3.5）
└── marketing/            # マーケティング生成ツール
    ├── __init__.py
    └── generator.py      # SNSコンテンツ生成ロジック
```

## 実装詳細

### Mission Uploader (`deploy/uploader.py`)

**機能:**
- ドラフトJSONファイルを読み込み、Supabaseデータベースの`challenges`テーブルに登録
- JSON形式からDBカラム形式への自動マッピング
- Upsert操作（既存レコードは更新、新規レコードは挿入）

**マッピングロジック:**
- `mission_id` → `id` (Primary Key)
- `narrative.story_hook` の最初の文 → `title` (100文字制限)
- `narrative.story_hook` → `description`
- `difficulty` → `difficulty`
- `environment.cost_token` → `points`
- `environment.image` → `image_name`
- `environment.internal_port` → `internal_port` (デフォルト: 8000)
- JSON全体 → `metadata` (jsonb型)
- `status` → `"active"` (即座にプレイ可能にするため)

**エラーハンドリング:**
- ファイル不在: 明確なエラーメッセージ
- JSONパースエラー: 詳細なエラー情報
- データベース接続エラー: 適切なメッセージ
- 権限エラー: 明確なメッセージ
- スキーマエラー: カラム不存在時の詳細メッセージ

### Mission Drafter (`generation/drafter.py`)

**機能:**
- OpenAI API (GPT-4o) を使用して、PROJECT_MASTER.mdのSchemaに完全準拠したJSONを生成
- System PromptとUser Promptを設計し、AIに正確な指示を送信
- 生成直後に自動検証を実行し、検証通過時のみファイルを保存
- 難易度計算式に準拠した`difficulty_factors`を自動生成

**生成されるフィールド:**
- `mission_id`: `SOL-MSN-{4桁の識別子}` 形式
- `mission_version`: `1.0.0` 固定
- `difficulty`: 1-5（指定可能、またはランダム）
- `difficulty_factors`: 難易度計算式に準拠した値
- `narrative.story_hook`: 禁止用語を含まない、最大3文のテキスト（Combat Mode）
- その他すべての必須フィールド

**AI統合:**
- System Prompt: サイバーセキュリティ専門家としての役割定義、JSON Schema、制約事項を明確に指示
- User Prompt: 難易度とタイプを指定し、具体的な問題作成を依頼
- Response Format: `json_object`形式で確実なJSONを取得

**自己検証とリトライ:**
- 生成直後に`MissionValidator`で検証
- 検証失敗時は自動リトライ（最大3回、`--max-retries`で変更可能）
- 検証通過時のみ`challenges/drafts/`に保存

**エラーハンドリング:**
- API認証エラー: 明確なエラーメッセージを表示
- レート制限エラー: 適切なエラーメッセージを表示
- JSONパースエラー: リトライを実行
- 検証エラー: 詳細を表示（`--verbose`時）

### CI Validator (`ci/validator.py`)

**機能:**
- JSON Schema検証（PROJECT_MASTER.md Section 4準拠）
- 難易度計算式検証（DIFFICULTY_SPEC.md Section 1準拠）
- Forbidden Wordsチェック（CONTENT_PLAN.md Section 1準拠）
- セキュリティ基準チェック（PROJECT_MASTER.md Section 5準拠）

**検証ルール:**
- `mission_id`: `SOL-MSN-XXX` 形式
- `mission_version`: SemVer形式（MAJOR.MINOR.PATCH）
- `type`: 許可されたタイプのみ（RCE, SQLi, SSRF等）
- `difficulty`: 1-5の整数、難易度計算式と一致
- `difficulty_factors`: tech, read, explore が各1-5の整数
- `cost_token`: 1000-10000の整数
- `expected_solve_time`: `^[0-9]+m$` 形式（例: "45m"）
- `story_hook`: 最大3文、Forbidden Wordsなし
- `tone`: "combat" のみ

### Marketing Generator (`marketing/generator.py`)

**機能:**
- SNS Teaser生成（Intel Mode、CONTENT_PLAN.md Section 4.B準拠）
- Mission Briefing生成（Combat Mode、CONTENT_PLAN.md Section 4.A準拠）

**生成フォーマット:**

**SNS Teaser:**
```
[MISSION ALERT]
Target: {Type} (CVE-XXXX-XXXX)
Level: {Difficulty}/5

Intel suggests a severe vulnerability.
{Commentary}

Dive in: {URL}
#ProjectSol
```

**Mission Briefing:**
```
=== MISSION BRIEFING ===
**Mission ID:** {SOL-MSN-XXX}
**Objective:** {Objective}
**Threat Level:** {1-5}

**Intel:**
{Story Hook}

[COMMAND] Proceed: Y / Abort: N
```

## テスト

サンプルデータを使用したテスト:

```bash
# ドラフト生成テスト
python3 tools/cli.py draft
python3 tools/cli.py draft --difficulty 5

# デプロイテスト（環境変数設定が必要）
python3 tools/cli.py deploy challenges/drafts/SOL-MSN-XXXX.json

# 検証テスト
python3 tools/cli.py validate challenges/samples/valid_mission.json
python3 tools/cli.py validate challenges/drafts/SOL-MSN-XXXX.json

# 生成テスト
python3 tools/cli.py generate challenges/samples/valid_mission.json sns
python3 tools/cli.py generate challenges/samples/valid_mission.json briefing
```

## エラーハンドリング

### Draftコマンド
- **API認証エラー**: `OPENAI_API_KEY`が設定されていない、または無効な場合に明確なメッセージを表示
- **レート制限エラー**: APIレート制限に達した場合の適切なメッセージ
- **JSONパースエラー**: AIからの応答がJSONとして解析できない場合、自動リトライ
- **検証エラー**: 生成されたJSONが検証を通過しない場合、自動リトライ（最大3回）

### Deployコマンド
- **データベース接続エラー**: Supabase URLやネットワーク接続の問題を検出
- **権限エラー**: Service Keyの権限不足を明確に表示
- **スキーマエラー**: テーブルカラム不存在時の詳細メッセージ
- **ファイル不在**: ユーザーフレンドリーなエラーメッセージを表示
- **JSONパースエラー**: 詳細なエラー情報を表示

### 共通
- **その他のエラー**: 詳細なエラー情報とスタックトレースを表示（`--verbose`時）

## 実装済みフェーズ

- ✅ Phase 2: Draft Generation（ドラフト生成）
- ✅ Phase 3: Auto-Validation（自動検証）
- ✅ Phase 3.5: DB Deployment（データベースデプロイ）

## 今後の拡張予定

- Phase 1: Trend Watch & Filter（CVE監視）
- Phase 4: Human Review（レビューキュー）

## 参照ドキュメント

- `PROJECT_MASTER.md`: システムアーキテクチャ、JSON Schema、Security Standards
- `DIFFICULTY_SPEC.md`: 難易度計算式、採点基準
- `CONTENT_PLAN.md`: コンテンツ生成ルール、禁止用語

---

**Version:** 10.2  
**Last Updated:** 2025-01

