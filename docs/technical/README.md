# 技術仕様書・設計資料

このディレクトリには、Project Solの技術的な詳細を記した資料が含まれています。

## 📁 主要な資料

### 設計書

- **自動問題生成アルゴリズム選定と開発指示.txt**: 
  - HyRAG-QGアーキテクチャの理論的基盤
  - Gemini APIとローカルLLMのハイブリッド戦略
  - 日本語処理の最適化手法
  - **重要**: このファイルがシステム全体の設計方針を定義しています

### 実装レポート

- **IMPLEMENTATION_REPORT.md**: 
  - 最新の修正内容（FILE PERSISTENCE RULE、WORKDIR/COPY順序修正など）
  - コード付きの詳細な説明
  - 実行結果と検証
  - 作成方針との整合性チェック

## 🎯 使用方法

### 開発を始める場合

1. `自動問題生成アルゴリズム選定と開発指示.txt`を読んで、システム全体の設計方針を理解
2. `IMPLEMENTATION_REPORT.md`で最新の実装状況を確認
3. 必要に応じて`docs/operations/PROJECT_MASTER.md`でJSON Schemaやセキュリティ基準を確認

### 修正を加える場合

1. `IMPLEMENTATION_REPORT.md`で過去の修正内容を確認
2. `自動問題生成アルゴリズム選定と開発指示.txt`で設計方針との整合性を確認
3. 修正後、`IMPLEMENTATION_REPORT.md`を更新

## 📚 関連ディレクトリ

- `docs/ai-handover/`: 監督用AI向け引継ぎ資料
- `docs/user-guides/`: ユーザー向け説明資料
- `docs/operations/`: 運用マニュアル

## 🔄 更新履歴

- 2025-01: IMPLEMENTATION_REPORT.md追加、ディレクトリ整理

