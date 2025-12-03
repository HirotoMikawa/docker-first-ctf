# Project Sol: AI問題生成アルゴリズム リサーチ依頼資料

**作成日**: 2024年
**バージョン**: 10.2
**目的**: 外部AI（ディープリサーチ）による問題生成アルゴリズムの改善提案のための包括的資料

---

## 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [現在の技術スタック](#現在の技術スタック)
3. [現在のアルゴリズムの詳細](#現在のアルゴリズムの詳細)
4. [既存の問題点と課題](#既存の問題点と課題)
5. [改善の方向性](#改善の方向性)
6. [リサーチの方向性](#リサーチの方向性)
7. [参考情報](#参考情報)

---

## プロジェクト概要

### プロジェクト名
**Project Sol** (CodeName: Docker-First CTF)

### ミッション
日本の理系学生・若手エンジニアに対し、インフラ構築・防御・コンテナ技術を「物語（Story）」の中で学べる没入型実践環境を提供する。

### コアコンセプト
- **Role**: ユーザーは「セキュリティ機関のエージェント」として参加
- **Action**: 単なる "Question" ではなく "Mission" を遂行する
- **Gamification**: UI/UXを通じて没入感を高め、学習の苦痛を取り除く
- **Solopreneur Philosophy**: 管理者（User）は「AIの手足」となり、意思決定と物理的な実装操作に徹する

### システムの目的
CTF（Capture The Flag）問題を**自動生成**し、Dockerコンテナとして提供するシステム。各問題は：
- 脆弱性を含むWebアプリケーション（Flask等）
- Dockerコンテナとしてパッケージ化
- 実際に動作し、実際に解ける問題
- 詳細な解説（writeup）付き

### 問題タイプ
- **RCE** (Remote Code Execution)
- **SQLi** (SQL Injection)
- **SSRF** (Server-Side Request Forgery)
- **XXE** (XML External Entity)
- **IDOR** (Insecure Direct Object Reference)
- **PrivEsc** (Privilege Escalation)
- **LogicError** (Logic Error / Crypto)
- **Misconfig** (Misconfiguration)

### 難易度システム
- **Difficulty**: 1-5（整数）
- **Difficulty Factors**:
  - **Tech**: 技術的複雑度（1-5）
  - **Read**: コード量・可読性（1-5）
  - **Explore**: 探索ステップ数（1-5）
- **計算式**: `Difficulty = Clamp(Round(Tech * 0.4 + Read * 0.2 + Explore * 0.4), 1, 5)`

---

## 現在の技術スタック

### フロントエンド
- **Next.js 14** (App Router)
- **Tailwind CSS**
- **shadcn/ui** (Radix UI + Tailwind CSS)

### バックエンド
- **FastAPI** (Python 3.11)
- **Docker SDK** (コンテナ管理)
- **slowapi** (レート制限)

### データベース
- **Supabase** (PostgreSQL + Auth)

### インフラ
- **VPS** (Ubuntu)
- **Docker Engine** (Rootless preferred)

### AI/ML
- **OpenAI GPT-4o** (問題生成と解説生成)

### 開発ツール
- **Python 3.11**
- **Docker** (コンテナビルド・実行)
- **Git** (バージョン管理)

---

## 現在のアルゴリズムの詳細

### 全体フロー（8ステップ）

```
[1/8] ドラフト生成（writeupなし）
  ├─ AI (GPT-4o) に問題生成を依頼
  ├─ System Prompt: 問題生成のルールと制約
  ├─ User Prompt: 難易度、タイプ、カテゴリ、テーマ
  └─ JSON Schema準拠のJSONを生成
  ↓
[2/8] Dockerfile検証
  ├─ ユーザー作成チェック（dockerfile_validator.py）
  └─ フラグ配置チェック（flag_placement_validator.py）
  ↓
[3/8] Dockerイメージビルド
  └─ docker build でイメージをビルド
  ↓
[4/8] テストコンテナ起動と検証
  ├─ コンテナ起動（docker run）
  ├─ 内部検査（docker exec）でフラグの存在確認
  └─ 機能テスト（problem_solver.py）で実際の解法確認
  ↓
[5/8] 解説（writeup）再生成
  ├─ 実際のコンテナURLを使用
  ├─ 探索ベースの解法を生成
  └─ 環境情報（データベース構造等）を含める
  ↓
[6/8] JSONファイル保存
  └─ challenges/drafts/ に保存
  ↓
[7/8] デプロイ（Supabase）
  └─ データベースに問題を登録
  ↓
[8/8] SNSコンテンツ生成
  └─ マーケティング用コンテンツを生成
```

### 問題生成アルゴリズム（`drafter.py`）

#### 1. プロンプト構築

**System Prompt** (`_build_system_prompt()`):
- **基本役割**: CTFアーキテクトとしての役割定義
- **JSON Schema**: 生成するJSONの構造（必須フィールド、型、制約）
- **重要な制約**:
  - 難易度計算式
  - 禁止用語（"Great", "Good luck", "Happy", "Sorry", "Please", "I think", "Feel", "Hope", "!"）
  - story_hook（最大3文、Combat Mode）
  - mission_id（"SOL-MSN-" + 4文字の英数字）
- **[CRITICAL: FLAG PLACEMENT STANDARDS]**: フラグ配置の決定木
  - RCE/LFI/PrivEsc/Misconfig → `/home/ctfuser/flag.txt`
  - SQLi/XSS/SSRF/XXE/IDOR → `/flag.txt` + `ENV FLAG`
  - LogicError/Crypto → 柔軟（コードまたはファイル）
- **[CRITICAL DOCKERFILE USER CREATION]**: ユーザー作成のルール
  - `python:3.11-slim` → `RUN useradd -m -u 1000 ctfuser`（`-s /bin/bash`なし）
  - `alpine:3.19` → `RUN adduser -D -u 1000 ctfuser`
- **[CRITICAL CONSTRAINTS FOR PYTHON APP]**: Flaskアプリの制約
  - ポート8000、ホスト0.0.0.0
  - ルートルートの定義
  - `render_template_string`の使用方法（文字列フォーマット）
- **SQLi問題の特別要件**: データベース初期化、エラーハンドリング
- **RCE問題の特別要件**: `sudo`の使用禁止、コマンド実行の制約

**User Prompt** (`_build_user_prompt()`):
- 難易度、タイプ、カテゴリ、テーマ
- フラグ配置のリマインダー（問題タイプに応じて）
- ストーリー性とデザインの要求

#### 2. AI API呼び出し

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

#### 3. 自動修正（Post-processing）

**`_fix_flag_placement()`**:
- フラグ配置を問題タイプに応じて自動修正
- Dockerfileの`RUN echo`コマンドを修正

**`_fix_database_initialization()`**:
- SQLi問題のデータベース初期化を自動追加
- `init_db()`関数、`CREATE TABLE users`、`INSERT INTO users`を追加

**`_fix_render_template_string()`**:
- Flaskの`render_template_string`を正しい形式に修正
- 文字列フォーマット（`.format()`）を使用する形式に変換

#### 4. 検証

- **JSON Schema検証**: `ci.validator.py`で検証
- **Dockerfile検証**: `validation/dockerfile_validator.py`で検証
- **フラグ配置検証**: `validation/flag_placement_validator.py`で検証

### 解説生成アルゴリズム（`regenerate_writeup()`）

#### 1. プロンプト構築

**System Prompt**:
- **基本役割**: CTF解説記事の専門家
- **[CRITICAL: EXPLORATION-BASED METHODOLOGY]**: 探索ベースの解法
  - 基本形の操作から始める
  - 失敗した場合の探索プロセス（複数の手順を紹介）
  - 発見と解決
  - 環境情報の説明（データベース構造、ファイル構造、権限）
  - 教育的価値の説明
- **構造（詳細版）**: Introduction、Environment Overview、Methodology、Mitigation、Key Takeaways
- **出力形式**: Markdown形式、適切な改行

**User Prompt**:
- **解く側の視点**: ソースコードを見ることができない
- **探索ベースの解法**: 複数の手順を紹介
- **環境情報**: データベース構造、ファイル構造、権限
- **最終的なフラグ取得方法**: フラグそのものではなく、操作手順
- **HTML情報**: 解く側が見える情報のみ

#### 2. AI API呼び出し

```python
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

### 検証アルゴリズム

#### 1. Dockerfile検証（`dockerfile_validator.py`）

- `USER ctfuser`の前に`useradd`/`adduser`があるかチェック
- `-s /bin/bash`の使用を警告（python:3.11-slimにはbashがない）

#### 2. フラグ配置検証（`flag_placement_validator.py`）

- 問題タイプに応じたフラグ配置をチェック
- 期待されるフラグ値がDockerfileに含まれているか

#### 3. コンテナテスト（`container_tester.py`）

**内部検査**:
- `docker exec`でフラグの存在確認
  - `/home/ctfuser/flag.txt`
  - `/flag.txt`
  - `env`出力
  - `$FLAG`環境変数

**機能テスト**（`problem_solver.py`）:
- **SQLi問題**: `solve_sqli()` - 一般的なSQLiペイロードを試行
- **RCE問題**: `solve_rce()` - 一般的なRCEペイロードを試行
- **LogicError問題**: `solve_logic_error()` - Caesar cipher等を試行

### 生成されるJSON構造

```json
{
  "mission_id": "SOL-MSN-XXXX",
  "mission_version": "1.0.0",
  "type": "RCE|SQLi|SSRF|...",
  "difficulty": 1-5,
  "difficulty_factors": {
    "tech": 1-5,
    "read": 1-5,
    "explore": 1-5
  },
  "vulnerability": {
    "cve_id": "CVE-YYYY-NNNN",
    "cvss": 0.0-10.0,
    "attack_vector": "Network|Local|Adjacent Network|Physical"
  },
  "environment": {
    "image": "sol/mission-xxx:latest",
    "base_image": "python:3.11-slim|alpine:3.19",
    "cost_token": 1000-10000,
    "expected_solve_time": "30m|45m|60m|90m|120m",
    "tags": ["web", "linux", ...]
  },
  "narrative": {
    "story_hook": "最大3文。禁止用語を含まない。",
    "tone": "combat"
  },
  "flag_answer": "SolCTF{...}",
  "files": {
    "app.py": "脆弱なアプリケーションコード（Python/Flask）",
    "Dockerfile": "Dockerfileの内容",
    "requirements.txt": "依存パッケージ（必要な場合）"
  },
  "writeup": "# 脆弱性の解説\n\n## 概要\n...\n\n## 解法手順\n...\n\n## 対策方法\n...\n\n## 学んだこと\n...",
  "tags": ["Web", "SQL", "Beginner"],
  "status": "draft"
}
```

---

## 既存の問題点と課題

### 1. プロンプトの複雑さと保守性

**問題**:
- System Promptが非常に長い（1000行以上）
- 複数のセクションが重複している可能性
- プロンプトの変更が困難（全体を理解する必要がある）
- プロンプトの効果を測定する仕組みがない

**影響**:
- プロンプトの改善が困難
- 新しい問題タイプの追加が困難
- プロンプトの最適化が困難

### 2. 自動修正の限界

**問題**:
- 3つの自動修正機能があるが、すべてのケースをカバーできていない
- AIが生成したコードの構造が予想外の場合、修正が失敗する可能性
- 修正が失敗した場合のフォールバック戦略がない
- 修正前後の差分をログに記録していない

**影響**:
- 問題生成の成功率が低い（再試行が必要）
- 手動修正が必要なケースが多い
- 修正ロジックの改善が困難

### 3. 検証ロジックの精度

**問題**:
- 内部検査と機能テストで検証しているが、すべての問題タイプをカバーできていない
- 誤検知（正常な問題を「解けない」と判定）の可能性
- 検証結果の詳細なログがない
- 検証失敗時の詳細なエラーメッセージがない

**影響**:
- 正常な問題が「解けない」と誤判定される
- 問題生成の成功率が低い
- デバッグが困難

### 4. 解説（writeup）の品質

**問題**:
- 探索ベースの解法を強調しているが、実際の生成結果が不十分な場合がある
- 環境情報の説明が不足している場合がある
- 解説の品質を評価するメトリクスがない
- 解説生成のプロンプトが複雑

**影響**:
- 解説の品質が不安定
- ユーザーが問題を解けない場合がある
- 解説の改善が困難

### 5. 問題生成の成功率

**問題**:
- 問題生成が失敗する場合がある（AIがJSON Schemaに準拠しない等）
- 再試行（max_retries=3）で解決する場合もあるが、時間がかかる
- 失敗原因の分析が困難
- 問題生成の成功率を追跡する仕組みがない

**影響**:
- 問題生成に時間がかかる
- コストが高い（AI API呼び出し）
- 問題生成の改善が困難

### 6. パフォーマンス

**問題**:
- 問題生成に時間がかかる（AI API呼び出し、Dockerビルド、検証等）
- 8ステップのフローで、1つの問題生成に数分かかる
- 並列処理がない
- キャッシュがない

**影響**:
- 問題生成のスループットが低い
- ユーザー体験が悪い
- スケーラビリティが低い

### 7. スケーラビリティ

**問題**:
- 問題タイプごとの専用ロジックがない
- 新しい問題タイプの追加が困難
- 問題タイプごとの最適化が困難

**影響**:
- 新しい問題タイプの追加が困難
- 問題タイプごとの品質が不安定

### 8. テストカバレッジ

**問題**:
- 問題生成のテストが不足している
- 自動修正機能のテストが不足している
- 検証ロジックのテストが不足している

**影響**:
- リグレッションのリスクが高い
- 改善が困難

---

## 改善の方向性

### 1. プロンプトエンジニアリングの改善

**現在のアプローチ**:
- 単一の長いSystem Prompt
- 問題タイプごとの条件分岐

**改善案**:
- **モジュール化**: プロンプトをモジュール化し、問題タイプごとに組み合わせる
- **Few-shot Learning**: 成功例をプロンプトに含める
- **Chain-of-Thought**: 段階的な思考プロセスを促す
- **プロンプトテンプレート**: 問題タイプごとの専用テンプレート
- **プロンプト最適化**: A/Bテストや自動最適化

### 2. アーキテクチャの改善

**現在のアプローチ**:
- 単一のAI API呼び出しで問題全体を生成
- 後処理で自動修正

**改善案**:
- **マルチステージ生成**: 問題生成を複数のステージに分割
  - Stage 1: 問題の設計（脆弱性タイプ、難易度、ストーリー）
  - Stage 2: コード生成（app.py、Dockerfile）
  - Stage 3: 検証と修正
  - Stage 4: 解説生成
- **専門化**: 各ステージに特化したAIモデルやプロンプト
- **フィードバックループ**: 検証結果を次の生成に反映

### 3. 検証とテストの改善

**現在のアプローチ**:
- 静的検証（Dockerfile検証、フラグ配置検証）
- 動的検証（コンテナテスト、機能テスト）

**改善案**:
- **包括的なテストスイート**: すべての問題タイプに対応
- **自動テスト生成**: 問題タイプごとのテストケースを自動生成
- **継続的検証**: 問題生成中にリアルタイムで検証
- **メトリクス収集**: 検証結果をメトリクスとして収集・分析

### 4. 解説生成の改善

**現在のアプローチ**:
- 単一のAI API呼び出しで解説を生成
- 探索ベースの解法を強調

**改善案**:
- **段階的解説生成**: 解法手順を段階的に生成
- **環境情報の自動抽出**: コンテナから環境情報を自動抽出
- **解説の品質評価**: 解説の品質を自動評価
- **解説の最適化**: ユーザーフィードバックを基に最適化

### 5. パフォーマンスの最適化

**現在のアプローチ**:
- シーケンシャルな処理
- キャッシュなし

**改善案**:
- **並列処理**: 複数の問題を並列生成
- **キャッシュ**: 類似問題の生成結果をキャッシュ
- **非同期処理**: 長時間かかる処理を非同期化
- **バッチ処理**: 複数の問題をバッチで生成

### 6. スケーラビリティの改善

**現在のアプローチ**:
- 問題タイプごとの条件分岐
- 単一の生成ロジック

**改善案**:
- **プラグインアーキテクチャ**: 問題タイプごとのプラグイン
- **設定駆動**: 問題タイプごとの設定ファイル
- **テンプレートシステム**: 問題タイプごとのテンプレート

### 7. モニタリングと分析

**現在のアプローチ**:
- ログ出力のみ
- メトリクス収集なし

**改善案**:
- **メトリクス収集**: 問題生成の成功率、時間、コスト等を収集
- **ダッシュボード**: メトリクスを可視化
- **アラート**: 問題生成の失敗を検知
- **分析**: メトリクスを分析して改善点を特定

---

## リサーチの方向性

### 1. 問題生成アルゴリズムの研究

**調査すべき分野**:
- **Automated Code Generation**: コード生成の最新手法
- **Program Synthesis**: プログラム合成の研究
- **Adversarial Example Generation**: 敵対的例の生成
- **CTF Problem Generation**: CTF問題生成の既存研究
- **Educational Content Generation**: 教育コンテンツ生成の研究

**参考にすべきアルゴリズム**:
- **Genetic Algorithms**: 問題の進化的生成
- **Reinforcement Learning**: 問題生成の最適化
- **Transformer-based Models**: コード生成の最新モデル
- **Program Synthesis**: プログラム合成の手法

### 2. プロンプトエンジニアリングの研究

**調査すべき分野**:
- **Prompt Engineering Best Practices**: プロンプトエンジニアリングのベストプラクティス
- **Few-shot Learning**: 少数サンプル学習
- **Chain-of-Thought Prompting**: 段階的思考プロンプト
- **Prompt Optimization**: プロンプトの自動最適化
- **Multi-stage Prompting**: マルチステージプロンプト

**参考にすべき手法**:
- **AutoPrompt**: プロンプトの自動最適化
- **PromptChainer**: プロンプトのチェーン化
- **Few-shot Learning**: 成功例をプロンプトに含める
- **Chain-of-Thought**: 段階的な思考プロセス

### 3. 検証とテストの研究

**調査すべき分野**:
- **Automated Testing**: 自動テスト生成
- **Property-based Testing**: プロパティベーステスト
- **Fuzzing**: ファジング
- **Symbolic Execution**: シンボリック実行
- **Formal Verification**: 形式的検証

**参考にすべき手法**:
- **Property-based Testing**: プロパティベーステスト（QuickCheck等）
- **Fuzzing**: ファジング（AFL等）
- **Symbolic Execution**: シンボリック実行（KLEE等）
- **Formal Verification**: 形式的検証

### 4. 解説生成の研究

**調査すべき分野**:
- **Educational Content Generation**: 教育コンテンツ生成
- **Explanation Generation**: 説明生成
- **Tutorial Generation**: チュートリアル生成
- **Step-by-step Instruction Generation**: ステップバイステップ指示生成

**参考にすべき手法**:
- **Explanation Generation**: 説明生成の研究
- **Tutorial Generation**: チュートリアル生成の研究
- **Step-by-step Instruction**: ステップバイステップ指示の研究

### 5. パフォーマンス最適化の研究

**調査すべき分野**:
- **Parallel Processing**: 並列処理
- **Caching Strategies**: キャッシュ戦略
- **Batch Processing**: バッチ処理
- **Async Processing**: 非同期処理

**参考にすべき手法**:
- **Parallel Processing**: 並列処理（multiprocessing等）
- **Caching**: キャッシュ（Redis等）
- **Batch Processing**: バッチ処理
- **Async Processing**: 非同期処理（asyncio等）

### 6. アーキテクチャパターンの研究

**調査すべき分野**:
- **Microservices Architecture**: マイクロサービスアーキテクチャ
- **Plugin Architecture**: プラグインアーキテクチャ
- **Event-driven Architecture**: イベント駆動アーキテクチャ
- **Pipeline Architecture**: パイプラインアーキテクチャ

**参考にすべきパターン**:
- **Pipeline Pattern**: パイプラインパターン
- **Plugin Pattern**: プラグインパターン
- **Event-driven Pattern**: イベント駆動パターン
- **Microservices Pattern**: マイクロサービスパターン

---

## 参考情報

### プロジェクトドキュメント

- **PROJECT_MASTER.md**: システムアーキテクチャ・JSON Schema・Security Standards
- **CONTENT_PLAN.md**: 生成プロセス・禁止用語SSOT・パイプライン手順
- **DIFFICULTY_SPEC.md**: 難易度・採点基準の詳細
- **OPS_MANUAL.md**: 安全性・コスト・緊急対応

### 主要ファイル

- **`tools/generation/drafter.py`**: 問題生成の核心（1725行）
- **`tools/cli.py`**: CLIインターフェース（846行）
- **`tools/solver/container_tester.py`**: コンテナテスト（426行）
- **`tools/solver/problem_solver.py`**: 自動解法（289行）
- **`tools/validation/dockerfile_validator.py`**: Dockerfile検証（64行）
- **`tools/validation/flag_placement_validator.py`**: フラグ配置検証（65行）

### 技術スタック

- **Python 3.11**: バックエンド開発
- **OpenAI GPT-4o**: AI問題生成
- **Docker**: コンテナ管理
- **Supabase**: データベース
- **FastAPI**: APIフレームワーク
- **Next.js 14**: フロントエンド

### 既存の問題と解決策

詳細は `reoprt/PROBLEM_GENERATION_HANDOVER.md` を参照してください。

---

## リサーチ依頼事項

### 1. 問題生成アルゴリズムの改善

**質問**:
- 現在のアプローチ（単一のAI API呼び出し + 後処理）は最適か？
- より良いアプローチ（マルチステージ生成、専門化等）はあるか？
- 既存の研究やアルゴリズムで参考になるものはあるか？

### 2. プロンプトエンジニアリングの改善

**質問**:
- 現在のプロンプト（1000行以上）は最適か？
- より良いプロンプト構造（モジュール化、Few-shot Learning等）はあるか？
- プロンプトの自動最適化は可能か？

### 3. 検証とテストの改善

**質問**:
- 現在の検証ロジックは十分か？
- より包括的な検証手法（Property-based Testing、Fuzzing等）はあるか？
- 自動テスト生成は可能か？

### 4. 解説生成の改善

**質問**:
- 現在の解説生成は最適か？
- より良い解説生成手法（段階的生成、環境情報の自動抽出等）はあるか？
- 解説の品質評価は可能か？

### 5. パフォーマンスの最適化

**質問**:
- 現在のパフォーマンスは最適か？
- より良い最適化手法（並列処理、キャッシュ等）はあるか？
- スケーラビリティの改善は可能か？

### 6. 根本的な作り変え

**質問**:
- 現在のアーキテクチャは最適か？
- より良いアーキテクチャ（マイクロサービス、プラグイン等）はあるか？
- 根本から作り変えるべきか？

---

## 期待される成果

1. **問題生成アルゴリズムの改善提案**
   - 現在のアプローチの評価
   - より良いアプローチの提案
   - 実装の優先順位

2. **プロンプトエンジニアリングの改善提案**
   - 現在のプロンプトの評価
   - より良いプロンプト構造の提案
   - 実装の優先順位

3. **検証とテストの改善提案**
   - 現在の検証ロジックの評価
   - より包括的な検証手法の提案
   - 実装の優先順位

4. **解説生成の改善提案**
   - 現在の解説生成の評価
   - より良い解説生成手法の提案
   - 実装の優先順位

5. **パフォーマンス最適化の提案**
   - 現在のパフォーマンスの評価
   - より良い最適化手法の提案
   - 実装の優先順位

6. **根本的な作り変えの提案**
   - 現在のアーキテクチャの評価
   - より良いアーキテクチャの提案
   - 実装の優先順位と移行計画

---

## 注意事項

1. **既存のコードを尊重する**: 既存のコードとアーキテクチャを理解し、無理な変更を避ける
2. **実装可能性を考慮する**: 提案は実装可能で、コストと時間を考慮する
3. **段階的な改善を推奨する**: 一度にすべてを変えるのではなく、段階的な改善を推奨する
4. **メトリクスを重視する**: 改善の効果を測定できるメトリクスを提案する
5. **ドキュメントを更新する**: 提案に基づいてドキュメントを更新する

---

## 連絡先

質問や追加情報が必要な場合は、プロジェクトのドキュメントを参照するか、GitHubリポジトリを確認してください。

---

**この資料は、外部AI（ディープリサーチ）による問題生成アルゴリズムの改善提案のための包括的資料です。現在のアプローチの評価、より良いアプローチの提案、根本的な作り変えの提案を期待しています。**

