# 運用マニュアル

このディレクトリには、Project Solの運用に関するマニュアルが含まれています。

## 📁 ファイル一覧

### コア仕様書

- **PROJECT_MASTER.md**: 
  - システムアーキテクチャのRoot Definition
  - JSON Schema定義
  - セキュリティ基準
  - **重要**: 実装の「正」を定義するファイル

### 運用関連

- **OPS_MANUAL.md**: 
  - 安全性・コスト・緊急対応
  - デプロイ手順
  - トラブルシューティング

### コンテンツ関連

- **DIFFICULTY_SPEC.md**: 
  - 難易度の定義と採点基準
  - 難易度レベルの詳細

- **CONTENT_PLAN.md**: 
  - 生成プロセスの詳細
  - 禁止用語のSSOT（Single Source of Truth）
  - パイプライン手順

## 🎯 使用方法

### 実装時の参照

- **JSON Schema**: `PROJECT_MASTER.md`の「Mission JSON Schema」セクション
- **セキュリティ基準**: `PROJECT_MASTER.md`の「Security Standards」セクション
- **難易度定義**: `DIFFICULTY_SPEC.md`

### 運用時の参照

- **デプロイ**: `OPS_MANUAL.md`
- **コンテンツ生成**: `CONTENT_PLAN.md`

## 📚 関連ディレクトリ

- `docs/technical/`: 技術仕様書（設計方針）
- `docs/user-guides/`: ユーザー向け説明資料
- `docs/ai-handover/`: 監督用AI向け引継ぎ資料

## 🔄 更新履歴

- 2025-01: ディレクトリ整理

