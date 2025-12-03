# Project Sol: 今後の予定（引継ぎ資料）

## 概要

Project Sol Ver 10.2 への移行が完了したため、次のフェーズとして以下の2つの自動化フローを実装する予定です。

## 1. 自動問題追加フロー

### 目的

新しいCTF問題を自動的に生成・検証・デプロイするパイプラインを構築し、コンテンツ更新の手作業を削減する。

### 実装予定の機能

#### Phase 1: Trend Watch & Filter
- **機能:** 最新のCVE情報やセキュリティトレンドを監視
- **フィルタ:** `PROJECT_MASTER.md` の "Disallowed CVE Types" に該当する脆弱性を除外
- **実装方法:**
  - CVEデータベース（NVD等）のAPIを定期ポーリング
  - フィルタリングロジックで許可された脆弱性タイプのみを抽出

#### Phase 2: Draft Generation
- **機能:** AIを使用して問題のドラフトを自動生成
- **モード:** COMBAT MODE（`CONTENT_PLAN.md` 準拠）
- **スキーマ:** `PROJECT_MASTER.md` の Master JSON Schema に100%準拠
- **制約:**
  - `narrative.story_hook` にForbidden Wordsを含めない
  - 難易度計算式に準拠（`DIFFICULTY_SPEC.md` 参照）
- **生成物:**
  - Dockerfile
  - 脆弱なアプリケーションコード
  - 問題説明文（Narrative）
  - メタデータ（JSON Schema準拠）

#### Phase 3: Auto-Validation (CI)
- **機能:** 生成された問題を自動検証
- **環境:** 固定バージョン（Python 3.11, Node 18）
- **チェック項目:**
  1. **Build Success:** Dockerイメージのビルドが成功するか
  2. **Security Standards Check:** Red-Team Security Standards に準拠しているか
     - リソース制限の確認
     - ネットワーク分離の確認
     - 非rootユーザー実行の確認
  3. **Exploit Success Rate:** エクスプロイトが正常に動作するか
     - Diff 1-2: 3/3 Success (100%)
     - Diff 3-4: 2/3 Success (>66%)
     - Diff 5: 1/3 Success (>33%)
  4. **Schema Check:** JSON Schema に準拠しているか
     - Regex チェック
     - 範囲チェック
  5. **Forbidden Word Check:** `story_hook` に禁止語が含まれていないか
     - 機械的にgrepでチェック

#### Phase 4: Human Review
- **機能:** 人間による最終レビュー
- **基準:**
  - Fun Factor（楽しさ）
  - Narrative Fit（物語との整合性）
- **ステータス遷移:** `draft` → `active`

### 実装アーキテクチャ（予定）

```
┌─────────────────┐
│  Trend Watch    │  CVE監視・フィルタリング
│   (Scheduler)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI Generator   │  問題ドラフト生成
│  (LLM API)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CI Pipeline    │  自動検証
│  (GitHub Actions│  - Build
│   / Self-hosted)│  - Security Check
│                 │  - Exploit Test
│                 │  - Schema Validation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Review Queue   │  人間によるレビュー待ち
│  (Supabase)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Auto Deploy    │  承認後の自動デプロイ
│  (Docker Build) │
└─────────────────┘
```

### 技術スタック（予定）

- **Scheduler:** APScheduler または Cron
- **CVE Data Source:** NVD API または CVE Database
- **AI Generation:** OpenAI API / Anthropic Claude API
- **CI/CD:** GitHub Actions または Self-hosted Runner
- **Validation:** Python + Docker SDK
- **Review Queue:** Supabase (PostgreSQL)

### 実装優先度

1. **High:** Phase 3 (Auto-Validation) - 既存の問題を検証する仕組み
2. **Medium:** Phase 2 (Draft Generation) - AI生成のプロトタイプ
3. **Low:** Phase 1 (Trend Watch) - 手動での問題追加から開始

---

## 2. SNSマーケティング自動化フロー

### 目的

専用のAIを使用して、SNS（Twitter/X、Mastodon等）への投稿を自動化し、マーケティング活動の負荷を削減する。

### 実装予定の機能

#### Phase 1: Content Generation
- **機能:** 問題リリースやアップデート情報をSNS投稿用のテキストに変換
- **モード:** Intel Mode（`CONTENT_PLAN.md` 準拠）
- **生成物:**
  - 問題紹介のテキスト
  - ハッシュタグ（#ProjectSol等）
  - リンク（問題URL）
- **制約:**
  - Forbidden Words を含めない
  - Combat Mode のトーンを維持
  - 文字数制限（Twitter: 280文字、Mastodon: 500文字等）

#### Phase 2: Scheduling
- **機能:** 投稿スケジュールの管理
- **頻度:** 
  - Daily: SNS Post (Intel Mode) - `OPS_MANUAL.md` 準拠
  - Weekly: New Mission Release の告知
- **実装方法:**
  - APScheduler または Cron で定期実行
  - Supabase にスケジュール情報を保存

#### Phase 3: Multi-Platform Posting
- **機能:** 複数のSNSプラットフォームに同時投稿
- **対応プラットフォーム（予定）:**
  - Twitter/X (API v2)
  - Mastodon (ActivityPub)
  - Bluesky (ATProtocol)
- **実装方法:**
  - 各プラットフォームのAPIを使用
  - 認証情報は環境変数で管理

#### Phase 4: Analytics & Optimization
- **機能:** 投稿の効果測定と最適化
- **メトリクス:**
  - エンゲージメント率
  - クリック率
  - フォロワー増加率
- **最適化:**
  - 投稿時刻の最適化
  - ハッシュタグの最適化
  - コンテンツのA/Bテスト

### 実装アーキテクチャ（予定）

```
┌─────────────────┐
│  Content DB     │  問題情報・リリース情報
│  (Supabase)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI Generator   │  SNS投稿テキスト生成
│  (LLM API)      │  (Intel Mode)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Scheduler      │  投稿スケジュール管理
│  (APScheduler)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Post Manager   │  複数プラットフォーム対応
│  - Twitter/X    │
│  - Mastodon     │
│  - Bluesky      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Analytics      │  効果測定・最適化
│  (Supabase)     │
└─────────────────┘
```

### 技術スタック（予定）

- **Content Generation:** OpenAI API / Anthropic Claude API
- **Scheduler:** APScheduler
- **Twitter/X API:** tweepy または twitter-api-v2
- **Mastodon API:** mastodon.py
- **Bluesky API:** atproto
- **Analytics:** Supabase (PostgreSQL) + カスタムダッシュボード

### 実装優先度

1. **High:** Phase 1 (Content Generation) - 基本的な投稿生成
2. **Medium:** Phase 2 (Scheduling) - 定期投稿の自動化
3. **Low:** Phase 3 (Multi-Platform) - 単一プラットフォームから開始
4. **Future:** Phase 4 (Analytics) - 基本機能実装後に追加

---

## 実装スケジュール（予定）

### Phase 1: 自動問題追加フローの基盤構築
- **期間:** 2-3週間
- **タスク:**
  - CI/CDパイプラインの構築
  - 自動検証ロジックの実装
  - レビューキューシステムの構築

### Phase 2: SNSマーケティング自動化のプロトタイプ
- **期間:** 1-2週間
- **タスク:**
  - AI生成ロジックの実装
  - 単一プラットフォーム（Twitter/X）への投稿機能
  - スケジューラーとの統合

### Phase 3: 本番運用への移行
- **期間:** 1週間
- **タスク:**
  - エラーハンドリングの強化
  - 監視・アラートの設定
  - ドキュメント整備

---

## 注意事項

### コスト管理
- AI API（OpenAI/Claude）の使用量に注意
- `OPS_MANUAL.md` のコスト制御基準に準拠
- 月額コストが ¥2,999 を超える場合、パイプラインが停止する仕様

### セキュリティ
- APIキーは環境変数で管理
- SNS APIの認証情報は暗号化して保存
- レート制限に注意

### 品質管理
- 自動生成されたコンテンツは必ず人間によるレビューを経る
- 問題の難易度バランスを維持
- Narrative のトーン（Combat Mode）を維持

---

**次のドキュメント:** [04_REFERENCE_FILES.md](./04_REFERENCE_FILES.md)

