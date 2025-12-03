# Project Sol: 引継ぎ資料ディレクトリ

## はじめに

このディレクトリには、Project Sol (Ver 10.2) の開発を引き継ぐための資料が含まれています。

**作成日:** 2025年1月  
**対象バージョン:** Ver 10.2 (Production Ready)  
**前バージョン:** Ver 5.0c (Prototype)

---

## 📋 ドキュメント一覧

### 1. [01_PROJECT_OVERVIEW.md](./01_PROJECT_OVERVIEW.md)
プロジェクトの概要、技術スタック、アーキテクチャ、セキュリティ基準を説明します。

**読むべき人:**
- プロジェクトを初めて知る人
- 全体像を素早く把握したい人

### 2. [02_CURRENT_STATUS.md](./02_CURRENT_STATUS.md)
現在の進捗状況、実装済み機能、既知の制約事項を説明します。

**読むべき人:**
- 現在の実装状況を確認したい人
- 次のタスクを決める人

### 3. [03_FUTURE_PLANS.md](./03_FUTURE_PLANS.md)
今後の予定（自動問題追加フロー、SNSマーケティング自動化）を説明します。

**読むべき人:**
- 次のフェーズの実装を担当する人
- プロジェクトの方向性を理解したい人

### 4. [04_REFERENCE_FILES.md](./04_REFERENCE_FILES.md)
参照すべきファイルの一覧と、新しいAIチャットに引き継ぐ際の推奨プロンプトを提供します。

**読むべき人:**
- 新しいAIチャットに引き継ぐ人
- どのファイルを参照すべきか迷っている人

---

## 🚀 クイックスタート

### 新しいAIチャットに引き継ぐ場合

1. **まず、このREADMEを読み込む**
   ```
   @docs/handover/00_README.md
   ```

2. **プロジェクトの全体像を理解する**
   ```
   @docs/handover/01_PROJECT_OVERVIEW.md
   ```

3. **現在の進捗状況を確認する**
   ```
   @docs/handover/02_CURRENT_STATUS.md
   ```

4. **今後の予定を確認する**
   ```
   @docs/handover/03_FUTURE_PLANS.md
   ```

5. **参照ファイル一覧を確認する**
   ```
   @docs/handover/04_REFERENCE_FILES.md
   ```

6. **最重要ファイルを読み込む**
   ```
   @PROJECT_MASTER.md @OPS_MANUAL.md @CONTENT_PLAN.md @DIFFICULTY_SPEC.md
   ```

### 詳細な引き継ぎプロンプト

`04_REFERENCE_FILES.md` に記載されている「推奨プロンプト例」を参照してください。

---

## 📊 プロジェクト状況サマリー

### ✅ 完了済み
- Ver 10.2 への移行完了
- バックエンド・フロントエンド・インフラの修正完了
- セキュリティ基準（Red-Team Standards）の実装
- 環境変数による動的接続先設定

### 🔄 進行中
- なし（移行完了）

### 📅 今後の予定
1. **自動問題追加フロー**の実装
   - Phase 1: Trend Watch & Filter
   - Phase 2: Draft Generation
   - Phase 3: Auto-Validation (CI)
   - Phase 4: Human Review

2. **SNSマーケティング自動化**の実装
   - Phase 1: Content Generation
   - Phase 2: Scheduling
   - Phase 3: Multi-Platform Posting
   - Phase 4: Analytics & Optimization

---

## 🔍 重要な注意事項

### コスト管理
- 月額コストが ¥2,999 を超える場合、パイプラインが停止する仕様
- 詳細は `OPS_MANUAL.md` を参照

### セキュリティ
- Red-Team Security Standards に準拠
- 詳細は `PROJECT_MASTER.md` の「5. Red-Team Security Standards」を参照

### コンテンツ生成
- Forbidden Words を含めない
- Combat Mode のトーンを維持
- 詳細は `CONTENT_PLAN.md` を参照

---

## 📞 サポート

質問や不明点がある場合は、以下のファイルを参照してください：

- **システムアーキテクチャ:** `PROJECT_MASTER.md`
- **運用マニュアル:** `OPS_MANUAL.md`
- **コンテンツ生成ルール:** `CONTENT_PLAN.md`
- **難易度設定:** `DIFFICULTY_SPEC.md`
- **セットアップ手順:** `SETUP.md`

---

**最終更新:** 2025年1月  
**バージョン:** Ver 10.2

