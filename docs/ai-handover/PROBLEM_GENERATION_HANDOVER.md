# Project Sol: 問題生成アルゴリズム 引継ぎ資料

**作成日**: 2024年
**バージョン**: 10.2
**目的**: 問題生成アルゴリズムの再設計のための包括的な引継ぎ資料

---

## 目次

1. [問題生成フローの概要](#問題生成フローの概要)
2. [主要なファイルとその役割](#主要なファイルとその役割)
3. [これまでに発生した問題と解決策](#これまでに発生した問題と解決策)
4. [現在のプロンプト構造](#現在のプロンプト構造)
5. [自動修正機能](#自動修正機能)
6. [検証ロジック](#検証ロジック)
7. [改善が必要な点](#改善が必要な点)
8. [技術的な詳細](#技術的な詳細)

---

## 問題生成フローの概要

### 全体フロー（`cmd_auto_add`）

```
[1/8] ドラフト生成（writeupなし）
  ↓
[2/8] Dockerfile検証
  - ユーザー作成チェック（dockerfile_validator.py）
  - フラグ配置チェック（flag_placement_validator.py）
  ↓
[3/8] Dockerイメージビルド
  ↓
[4/8] テストコンテナ起動と検証
  - 内部検査（docker exec）でフラグの存在確認
  - 機能テスト（problem_solver.py）で実際の解法確認
  ↓
[5/8] 解説（writeup）再生成
  - 実際のコンテナURLを使用
  - 探索ベースの解法を生成
  ↓
[6/8] JSONファイル保存
  ↓
[7/8] デプロイ（Supabase）
  ↓
[8/8] SNSコンテンツ生成
```

### 主要なコマンド

- `python tools/cli.py auto-add --difficulty 3`: 自動生成フロー実行
- `python tools/cli.py reset`: 環境リセット（DB、Docker、JSONファイル削除）

---

## 主要なファイルとその役割

### 1. `tools/generation/drafter.py` - 問題生成の核心

**役割**: AI（GPT-4o）を使用してCTF問題のJSONを生成

**主要メソッド**:
- `draft()`: 問題生成のメインエントリーポイント
- `_build_system_prompt()`: AIへのシステムプロンプト構築
- `_build_user_prompt()`: AIへのユーザープロンプト構築
- `regenerate_writeup()`: 解説（writeup）の再生成
- `_fix_flag_placement()`: フラグ配置の自動修正
- `_fix_database_initialization()`: データベース初期化の自動修正
- `_fix_render_template_string()`: Flaskテンプレートの自動修正

**生成されるJSON構造**:
```json
{
  "mission_id": "SOL-MSN-XXXX",
  "type": "RCE|SQLi|SSRF|...",
  "difficulty": 1-5,
  "flag_answer": "SolCTF{...}",
  "files": {
    "app.py": "...",
    "Dockerfile": "...",
    "requirements.txt": "..."
  },
  "writeup": "# 解説..."
}
```

### 2. `tools/cli.py` - CLIインターフェース

**役割**: コマンドラインから問題生成フローを実行

**主要コマンド**:
- `cmd_auto_add()`: 自動生成フロー（8ステップ）
- `cmd_reset()`: 環境リセット（DB、Docker、JSONファイル削除）

### 3. `tools/solver/container_tester.py` - コンテナテスト

**役割**: 生成された問題が実際に解けるかを検証

**主要メソッド**:
- `start_test_container()`: テストコンテナを起動
- `test_solvability()`: 問題が解けるかを検証
  - 内部検査: `docker exec`でフラグの存在確認
  - 機能テスト: `problem_solver.py`で実際の解法確認

### 4. `tools/solver/problem_solver.py` - 自動解法

**役割**: 攻撃者の視点から問題を自動的に解く

**主要メソッド**:
- `solve_sqli()`: SQLインジェクション問題を解く
- `solve_rce()`: RCE問題を解く
- `solve_logic_error()`: LogicError問題を解く（Caesar cipher等）

### 5. `tools/validation/dockerfile_validator.py` - Dockerfile検証

**役割**: Dockerfileのユーザー作成を検証

**主要機能**:
- `USER ctfuser`の前に`useradd`/`adduser`があるかチェック
- `-s /bin/bash`の使用を警告（python:3.11-slimにはbashがない）

### 6. `tools/validation/flag_placement_validator.py` - フラグ配置検証

**役割**: 問題タイプに応じたフラグ配置を検証

**検証ルール**:
- RCE/LFI/PrivEsc/Misconfig → `/home/ctfuser/flag.txt`
- SQLi/XSS/SSRF/XXE/IDOR → `/flag.txt` + `ENV FLAG`
- LogicError/Crypto → 柔軟（コードまたはファイル）

---

## これまでに発生した問題と解決策

### 問題1: フラグ配置の不整合

**症状**: 
- RCE問題で`/flag.txt`にフラグを配置（正しくは`/home/ctfuser/flag.txt`）
- Web問題で`/home/ctfuser/flag.txt`にフラグを配置（正しくは`/flag.txt`）

**原因**: AIが問題タイプに応じたフラグ配置ルールを理解していない

**解決策**:
1. System Promptに`[CRITICAL: FLAG PLACEMENT STANDARDS]`セクションを追加
2. 決定木（Decision Tree）を追加して問題タイプごとのルールを明確化
3. `_fix_flag_placement()`メソッドで自動修正

**現在のルール**:
```
RCE/LFI/PrivEsc/Misconfig → /home/ctfuser/flag.txt
SQLi/XSS/SSRF/XXE/IDOR → /flag.txt + ENV FLAG
LogicError/Crypto → 柔軟
```

### 問題2: Dockerfileのユーザー作成エラー

**症状**: 
```
Docker API error: 500 Server Error
"unable to find user ctfuser: no matching entries in passwd file"
```

**原因**: 
- `python:3.11-slim`には`bash`がインストールされていない
- `RUN useradd -ms /bin/bash ctfuser`が失敗

**解決策**:
1. System Promptに`[CRITICAL DOCKERFILE USER CREATION]`セクションを追加
2. `python:3.11-slim`の場合は`RUN useradd -m -u 1000 ctfuser`（`-s /bin/bash`なし）
3. `alpine:3.19`の場合は`RUN adduser -D -u 1000 ctfuser`
4. `dockerfile_validator.py`で検証

### 問題3: SQLi問題のデータベース初期化エラー

**症状**: 
- `' OR 1=1 -- `を入力すると「Internal Server Error」
- 「no such table: users」エラー

**原因**: 
- `app.py`にデータベース初期化コード（`init_db()`）がない
- `users`テーブルが作成されていない

**解決策**:
1. System PromptにSQLi問題のデータベース初期化要件を追加
2. `_fix_database_initialization()`メソッドで自動修正
   - `init_db()`関数を追加
   - `CREATE TABLE users`を追加
   - `INSERT INTO users`でサンプルデータを追加
   - `app.run()`の前に`init_db()`を呼び出し

### 問題4: Flaskの`render_template_string`の変数渡しエラー

**症状**: 
- RCE問題で`http://localhost:32800/run?cmd=id`が白紙ページ
- SQLi問題で変数が表示されない

**原因**: 
- `render_template_string(template, user=user)`の形式が正しく動作しない
- 文字列フォーマット（`.format()`）を使用する必要がある

**解決策**:
1. System Promptに`[CRITICAL CONSTRAINTS FOR PYTHON APP]`セクションを追加
2. `render_template_string`は文字列フォーマット（`.format()`）を使用することを明記
3. `_fix_render_template_string()`メソッドで自動修正

**修正例**:
```python
# 修正前（動作しない）
template = "<h1>Hello {{ user }}</h1>"
return render_template_string(template, user=username)

# 修正後（動作する）
template = "<h1>Hello {}</h1>"
return render_template_string(template.format(username))
```

### 問題5: 解説（writeup）が解く側の視点ではない

**症状**: 
- 「コードを見るとわかる」という記述
- コード内の変数名（`SECRET_MESSAGE`）を参照
- 解く側には見えない情報を基にした解説

**原因**: 
- AIが制作側の視点で解説を生成している
- 解く側が見える情報（HTMLのみ）を考慮していない

**解決策**:
1. `regenerate_writeup()`のSystem Promptを改善
2. 「解く側の視点」を強調
3. 「コードを見るとわかる」という記述を禁止
4. HTMLから見える情報のみを基にした解説を生成

### 問題6: 解説が不十分（探索手順が少ない）

**症状**: 
- 解説が簡潔すぎる
- 探索手順が少ない
- 環境情報（データベース構造等）が記載されていない
- 改行が少なく読みにくい

**原因**: 
- 解説生成プロンプトが簡潔すぎる
- 探索ベースの解法を強調していない

**解決策**:
1. `regenerate_writeup()`のSystem Promptを大幅改善
2. `[CRITICAL: EXPLORATION-BASED METHODOLOGY]`セクションを追加
3. 環境情報セクション（Environment Overview）を追加
4. 複数の探索手順を紹介する指示を追加
5. 適切な改行の指示を追加
6. フラグそのものではなく、操作手順を記載する指示を追加

**改善された構造**:
```
- Introduction: 脆弱性とは何か？
- Environment Overview: 環境情報（データベース、ファイル構造、権限）
- Methodology: ステップバイステップの解法ガイド
  - Step 1: 基本形の操作を試す
  - Step 2: 失敗した場合の探索（複数の手順を紹介）
  - Step 3: 発見と解決（最終的な操作手順）
- Mitigation: 実際のコードで修正する方法
- Key Takeaways: 学んだことを箇条書きでまとめる
```

### 問題7: 検証ロジックが不十分

**症状**: 
- 正常な問題が「解けない」と誤判定される
- HTTPステータスコード200以外は即NG
- コンテナの起動完了を待たずに検証

**原因**: 
- 単純なHTTPチェックのみ
- コンテナの起動待機時間が不足

**解決策**:
1. `container_tester.py`を改善
2. 「Wait-for-Ready戦略」を実装（コンテナ起動を待機）
3. 「ヒューリスティックチェック」を実装（200以外でもフラグが見つかればOK）
4. 内部検査（`docker exec`）でフラグの存在確認
5. 機能テスト（`problem_solver.py`）で実際の解法確認

### 問題8: JSONファイルが削除されない

**症状**: 
- データベースをリセットしても`challenges/drafts/`のJSONファイルが残る
- ディスク容量を無駄に消費

**解決策**:
1. `cmd_reset()`にJSONファイル削除機能を追加
2. `challenges/drafts/`内のすべての`*.json`ファイルを削除

---

## 現在のプロンプト構造

### System Prompt（`_build_system_prompt()`）

**主要セクション**:

1. **基本役割**: CTFアーキテクトとしての役割定義
2. **JSON Schema**: 生成するJSONの構造
3. **重要な制約**: 難易度計算式、禁止用語、story_hook等
4. **[CRITICAL: FLAG PLACEMENT STANDARDS]**: フラグ配置の決定木とルール
5. **[CRITICAL DOCKERFILE USER CREATION]**: ユーザー作成のルール
6. **[CRITICAL CONSTRAINTS FOR PYTHON APP]**: Flaskアプリの制約
   - ポート8000、ホスト0.0.0.0
   - ルートルートの定義
   - `render_template_string`の使用方法
7. **SQLi問題の特別要件**: データベース初期化、エラーハンドリング
8. **RCE問題の特別要件**: `sudo`の使用禁止、コマンド実行の制約

### User Prompt（`_build_user_prompt()`）

**主要セクション**:

1. **問題生成の指示**: 難易度、タイプ、カテゴリ、テーマ
2. **フラグ配置のリマインダー**: 問題タイプに応じたフラグ配置を強調
3. **ストーリー性とデザイン**: 視覚的な没入感の要求

### Writeup生成プロンプト（`regenerate_writeup()`）

**System Prompt**:

1. **基本役割**: CTF解説記事の専門家
2. **[CRITICAL: EXPLORATION-BASED METHODOLOGY]**: 探索ベースの解法
   - 基本形の操作から始める
   - 失敗した場合の探索プロセス
   - 発見と解決
   - 環境情報の説明
   - 教育的価値の説明
3. **構造（詳細版）**: Introduction、Environment Overview、Methodology、Mitigation、Key Takeaways
4. **出力形式**: Markdown形式、適切な改行

**User Prompt**:

1. **解く側の視点**: ソースコードを見ることができない
2. **探索ベースの解法**: 複数の手順を紹介
3. **環境情報**: データベース構造、ファイル構造、権限
4. **最終的なフラグ取得方法**: フラグそのものではなく、操作手順
5. **HTML情報**: 解く側が見える情報のみ

---

## 自動修正機能

### 1. `_fix_flag_placement()`

**目的**: フラグ配置を問題タイプに応じて自動修正

**修正内容**:
- RCE/LFI/PrivEsc/Misconfig → `/home/ctfuser/flag.txt`に修正
- SQLi/XSS/SSRF/XXE/IDOR → `/flag.txt` + `ENV FLAG`に修正

**実装場所**: `tools/generation/drafter.py:647`

### 2. `_fix_database_initialization()`

**目的**: SQLi問題のデータベース初期化を自動追加

**修正内容**:
- `init_db()`関数を追加
- `CREATE TABLE users`を追加
- `INSERT INTO users`でサンプルデータを追加
- `app.run()`の前に`init_db()`を呼び出し

**実装場所**: `tools/generation/drafter.py:731`

### 3. `_fix_render_template_string()`

**目的**: Flaskの`render_template_string`を正しい形式に修正

**修正内容**:
- 文字列フォーマット（`.format()`）を使用する形式に変換
- `sudo -u root`を削除（ctfuserにsudo権限がない）

**実装場所**: `tools/generation/drafter.py:795`

---

## 検証ロジック

### 1. Dockerfile検証（`dockerfile_validator.py`）

**検証内容**:
- `USER ctfuser`の前に`useradd`/`adduser`があるか
- `-s /bin/bash`の使用を警告

**実行タイミング**: `cmd_auto_add()`のStep 2

### 2. フラグ配置検証（`flag_placement_validator.py`）

**検証内容**:
- 問題タイプに応じたフラグ配置をチェック
- 期待されるフラグ値がDockerfileに含まれているか

**実行タイミング**: `cmd_auto_add()`のStep 2

### 3. コンテナテスト（`container_tester.py`）

**検証内容**:
- コンテナの起動
- 内部検査（`docker exec`）でフラグの存在確認
  - `/home/ctfuser/flag.txt`
  - `/flag.txt`
  - `env`出力
  - `$FLAG`環境変数
- 機能テスト（`problem_solver.py`）で実際の解法確認
  - SQLi問題: `solve_sqli()`
  - RCE問題: `solve_rce()`
  - LogicError問題: `solve_logic_error()`

**実行タイミング**: `cmd_auto_add()`のStep 4

---

## 改善が必要な点

### 1. プロンプトの複雑さ

**現状**: 
- System Promptが非常に長い（1000行以上）
- 複数のセクションが重複している可能性

**改善案**:
- プロンプトをモジュール化
- 問題タイプごとに専用のプロンプトを用意
- プロンプトの効果を測定する仕組みを追加

### 2. 自動修正の限界

**現状**: 
- 3つの自動修正機能があるが、すべてのケースをカバーできていない
- AIが生成したコードの構造が予想外の場合、修正が失敗する可能性

**改善案**:
- より多くの自動修正機能を追加
- 修正が失敗した場合のフォールバック戦略
- 修正前後の差分をログに記録

### 3. 検証ロジックの精度

**現状**: 
- 内部検査と機能テストで検証しているが、すべての問題タイプをカバーできていない
- 誤検知（正常な問題を「解けない」と判定）の可能性

**改善案**:
- より多くの問題タイプに対応した解法ロジック
- 検証結果の詳細なログ
- 検証失敗時の詳細なエラーメッセージ

### 4. 解説（writeup）の品質

**現状**: 
- 探索ベースの解法を強調しているが、実際の生成結果が不十分な場合がある
- 環境情報の説明が不足している場合がある

**改善案**:
- 解説生成のプロンプトをさらに改善
- 生成された解説を検証する仕組み
- 解説の品質を評価するメトリクス

### 5. 問題生成の成功率

**現状**: 
- 問題生成が失敗する場合がある（AIがJSON Schemaに準拠しない等）
- 再試行（max_retries=3）で解決する場合もあるが、時間がかかる

**改善案**:
- より詳細なエラーメッセージ
- 失敗原因の分析と改善
- 問題生成の成功率を追跡する仕組み

### 6. パフォーマンス

**現状**: 
- 問題生成に時間がかかる（AI API呼び出し、Dockerビルド、検証等）
- 8ステップのフローで、1つの問題生成に数分かかる

**改善案**:
- 並列処理の導入
- キャッシュの活用
- 不要な検証ステップの削減

---

## 技術的な詳細

### AI API（OpenAI GPT-4o）

**使用箇所**:
- `tools/generation/drafter.py`: 問題生成と解説生成

**API呼び出し**:
```python
client = OpenAI(api_key=api_key)
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.7,
    max_tokens=8000
)
```

### Docker操作

**使用箇所**:
- `tools/builder/simple_builder.py`: イメージビルド
- `tools/solver/container_tester.py`: コンテナ起動とテスト

**主要操作**:
- `docker build`: イメージビルド
- `docker run`: コンテナ起動
- `docker exec`: コンテナ内でコマンド実行
- `docker port`: ポートマッピング取得

### データベース（Supabase）

**使用箇所**:
- `tools/deploy/uploader.py`: 問題のデプロイ

**主要操作**:
- `reset_database()`: データベースリセット
- `upload_mission()`: 問題のアップロード

### ファイル構造

```
my_ctf_product/
├── tools/
│   ├── generation/
│   │   └── drafter.py          # 問題生成
│   ├── solver/
│   │   ├── container_tester.py # コンテナテスト
│   │   └── problem_solver.py   # 自動解法
│   ├── validation/
│   │   ├── dockerfile_validator.py      # Dockerfile検証
│   │   └── flag_placement_validator.py # フラグ配置検証
│   ├── builder/
│   │   └── simple_builder.py   # Dockerイメージビルド
│   ├── deploy/
│   │   └── uploader.py         # Supabaseデプロイ
│   └── cli.py                  # CLIインターフェース
├── challenges/
│   └── drafts/                 # 生成されたJSONファイル
└── docs/
    └── PROBLEM_GENERATION_HANDOVER.md  # このファイル
```

---

## 次のステップ

### 推奨される改善作業

1. **プロンプトの再設計**
   - モジュール化
   - 問題タイプごとの専用プロンプト
   - プロンプトの効果測定

2. **自動修正機能の拡張**
   - より多くのケースに対応
   - 修正前後の差分ログ

3. **検証ロジックの改善**
   - より多くの問題タイプに対応
   - 検証結果の詳細なログ

4. **解説品質の向上**
   - 解説生成プロンプトの改善
   - 解説の品質評価メトリクス

5. **パフォーマンスの最適化**
   - 並列処理の導入
   - キャッシュの活用

---

## 参考資料

### 関連ファイル

- `tools/generation/drafter.py`: 問題生成の核心
- `tools/cli.py`: CLIインターフェース
- `tools/solver/container_tester.py`: コンテナテスト
- `tools/solver/problem_solver.py`: 自動解法
- `tools/validation/dockerfile_validator.py`: Dockerfile検証
- `tools/validation/flag_placement_validator.py`: フラグ配置検証

### 関連ドキュメント

- `PROJECT_MASTER.md`: プロジェクトの全体仕様
- `CONTENT_PLAN.md`: コンテンツ計画
- `DIFFICULTY_SPEC.md`: 難易度仕様

---

## まとめ

この引継ぎ資料は、Project Solの問題生成アルゴリズムの現状を包括的にまとめたものです。問題生成フロー、主要なファイル、これまでに発生した問題と解決策、現在のプロンプト構造、自動修正機能、検証ロジック、改善が必要な点、技術的な詳細を記載しています。

この資料を基に、問題生成アルゴリズムの再設計を進めることができます。特に、プロンプトの再設計、自動修正機能の拡張、検証ロジックの改善、解説品質の向上、パフォーマンスの最適化が推奨されます。

