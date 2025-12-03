# Project Sol: 参照ファイル一覧（引継ぎ資料）

## 重要度別ファイルリスト

新しいAIチャットに引き継ぐ際は、以下のファイルを**優先度順**にプロンプトとして与えることを推奨します。

---

## 🔴 最優先（必須）

これらのファイルは、プロジェクトの**Single Source of Truth (SSOT)** として機能します。必ず最初に読み込んでください。

### 1. `PROJECT_MASTER.md`
- **場所:** プロジェクトルート
- **内容:** システムアーキテクチャ、JSON Schema、Security Standards
- **重要度:** ⭐⭐⭐⭐⭐
- **理由:** プロジェクトのルート定義。全ての実装の基準となる。

### 2. `OPS_MANUAL.md`
- **場所:** プロジェクトルート
- **内容:** 安全性・コスト・緊急対応、パイプライン状態機械
- **重要度:** ⭐⭐⭐⭐⭐
- **理由:** 運用時の安全性とコスト管理の基準。最優先で理解すべき。

### 3. `CONTENT_PLAN.md`
- **場所:** プロジェクトルート
- **内容:** 生成プロセス、禁止用語SSOT、パイプライン手順
- **重要度:** ⭐⭐⭐⭐⭐
- **理由:** コンテンツ生成時のルール。自動問題追加フロー実装時に必須。

### 4. `DIFFICULTY_SPEC.md`
- **場所:** プロジェクトルート
- **内容:** 難易度計算式、採点基準の詳細
- **重要度:** ⭐⭐⭐⭐
- **理由:** 問題の難易度設定と検証時に必須。

---

## 🟡 高優先度（推奨）

### 5. `SETUP.md`
- **場所:** プロジェクトルート
- **内容:** フロントエンド・バックエンド・インフラのセットアップ手順
- **重要度:** ⭐⭐⭐⭐
- **理由:** 開発環境の構築とデプロイ時に必要。

### 6. `.cursorrules`
- **場所:** プロジェクトルート（または `planning/.cursorrules`）
- **内容:** AIアシスタントの動作ルール、参照優先順位、実装チェックリスト
- **重要度:** ⭐⭐⭐⭐
- **理由:** AIアシスタントがコードを生成・修正する際の基準。

---

## 🟢 中優先度（参考）

### 7. `docker-compose.yml`
- **場所:** プロジェクトルート
- **内容:** Docker Compose設定、サービス定義、環境変数
- **重要度:** ⭐⭐⭐
- **理由:** インフラ構成の理解に必要。

### 8. `api/app/main.py`
- **場所:** `api/app/main.py`
- **内容:** FastAPIアプリケーションのメインロジック
- **重要度:** ⭐⭐⭐
- **理由:** バックエンドの実装状況を理解するために必要。

### 9. `web/app/page.tsx`
- **場所:** `web/app/page.tsx`
- **内容:** フロントエンドのメインページ
- **重要度:** ⭐⭐⭐
- **理由:** フロントエンドの実装状況を理解するために必要。

### 10. `web/utils/api.ts`
- **場所:** `web/utils/api.ts`
- **内容:** APIクライアントユーティリティ
- **重要度:** ⭐⭐⭐
- **理由:** フロントエンドのAPI接続実装を理解するために必要。

---

## 📋 引継ぎ資料（本ディレクトリ）

### 11. `docs/handover/01_PROJECT_OVERVIEW.md`
- **内容:** プロジェクト概要、技術スタック、アーキテクチャ
- **重要度:** ⭐⭐⭐⭐
- **理由:** プロジェクトの全体像を素早く理解するために有用。

### 12. `docs/handover/02_CURRENT_STATUS.md`
- **内容:** 現在の進捗状況、実装済み機能、既知の制約事項
- **重要度:** ⭐⭐⭐⭐
- **理由:** 現在の実装状況を正確に把握するために必要。

### 13. `docs/handover/03_FUTURE_PLANS.md`
- **内容:** 今後の予定（自動問題追加フロー、SNSマーケティング自動化）
- **重要度:** ⭐⭐⭐⭐
- **理由:** 次のフェーズの実装計画を理解するために必要。

### 14. `docs/handover/04_REFERENCE_FILES.md`（本ファイル）
- **内容:** 参照ファイル一覧
- **重要度:** ⭐⭐⭐
- **理由:** どのファイルを参照すべきかのガイド。

---

## 📝 推奨プロンプト例

新しいAIチャットに引き継ぐ際は、以下のようなプロンプトを使用することを推奨します。

### 基本プロンプト

```
@PROJECT_MASTER.md @OPS_MANUAL.md @CONTENT_PLAN.md @DIFFICULTY_SPEC.md @SETUP.md

Project Sol (Ver 10.2) の開発を引き継ぎます。

まず、上記のファイルを読み込んで、プロジェクトの全体像を理解してください。
特に以下の点を確認してください：

1. PROJECT_MASTER.md: システムアーキテクチャ、JSON Schema、Security Standards
2. OPS_MANUAL.md: コスト管理基準、パイプライン状態機械
3. CONTENT_PLAN.md: コンテンツ生成ルール、禁止用語
4. DIFFICULTY_SPEC.md: 難易度計算式、採点基準

理解が完了したら、現在の進捗状況を確認するため、以下の引継ぎ資料も読み込んでください：

@docs/handover/01_PROJECT_OVERVIEW.md
@docs/handover/02_CURRENT_STATUS.md
@docs/handover/03_FUTURE_PLANS.md
```

### 詳細プロンプト（実装開始時）

```
@PROJECT_MASTER.md @OPS_MANUAL.md @CONTENT_PLAN.md @DIFFICULTY_SPEC.md @SETUP.md
@docs/handover/01_PROJECT_OVERVIEW.md
@docs/handover/02_CURRENT_STATUS.md
@docs/handover/03_FUTURE_PLANS.md
@docker-compose.yml
@api/app/main.py
@web/app/page.tsx
@web/utils/api.ts

Project Sol (Ver 10.2) の開発を引き継ぎます。

現在の状況：
- Ver 10.2 への移行は完了済み
- バックエンド・フロントエンド・インフラの修正は完了
- 次のフェーズとして、自動問題追加フローとSNSマーケティング自動化を実装予定

次のタスク：
1. 自動問題追加フローの実装（Phase 3: Auto-Validation から開始）
2. SNSマーケティング自動化の実装（Phase 1: Content Generation から開始）

実装を開始する前に、上記のファイルを全て読み込んで、プロジェクトの全体像を理解してください。
```

---

## 🔍 ファイル検索コマンド

プロジェクト内のファイルを検索する際は、以下のコマンドを使用できます。

```bash
# プロジェクトルートに移動
cd /home/aniosu/my_ctf_product

# Markdownファイルを検索
find . -name "*.md" -type f

# Pythonファイルを検索
find . -name "*.py" -type f

# TypeScript/TSXファイルを検索
find . -name "*.ts" -o -name "*.tsx" | grep -v node_modules
```

---

## 📚 追加リソース

### プロジェクト構造

```
my_ctf_product/
├── PROJECT_MASTER.md          # ⭐⭐⭐⭐⭐ 必須
├── OPS_MANUAL.md              # ⭐⭐⭐⭐⭐ 必須
├── CONTENT_PLAN.md            # ⭐⭐⭐⭐⭐ 必須
├── DIFFICULTY_SPEC.md         # ⭐⭐⭐⭐ 推奨
├── SETUP.md                   # ⭐⭐⭐⭐ 推奨
├── .cursorrules               # ⭐⭐⭐⭐ 推奨
├── docker-compose.yml         # ⭐⭐⭐ 参考
├── api/                       # バックエンド
│   └── app/
│       ├── main.py            # ⭐⭐⭐ 参考
│       ├── core/
│       │   ├── config.py
│       │   └── docker_manager.py
│       └── dependencies.py
├── web/                       # フロントエンド
│   └── app/
│       ├── page.tsx           # ⭐⭐⭐ 参考
│       └── login/
│   └── utils/
│       └── api.ts             # ⭐⭐⭐ 参考
├── challenges/                # CTF問題
│   └── sqli-01/
└── docs/                      # ドキュメント
    └── handover/              # 引継ぎ資料
        ├── 01_PROJECT_OVERVIEW.md
        ├── 02_CURRENT_STATUS.md
        ├── 03_FUTURE_PLANS.md
        └── 04_REFERENCE_FILES.md
```

---

**次のステップ:** 新しいAIチャットに上記のプロンプトを使用して、プロジェクトを引き継いでください。

