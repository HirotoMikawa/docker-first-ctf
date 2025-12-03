# Project Sol: ドキュメント一覧

このディレクトリには、Project Solのすべてのドキュメントが整理されています。

## 📁 ディレクトリ構成

```
docs/
├── README.md (このファイル)
├── ai-handover/      # 監督用AI向け引継ぎ資料
├── user-guides/      # ユーザー向け詳細説明資料
├── technical/        # 技術仕様書・設計資料
└── operations/       # 運用マニュアル
```

## 🎯 各ディレクトリの目的

### `ai-handover/` - 監督用AI向け引継ぎ資料

AIアシスタント（Cursor、Gemini Canvas等）が開発を継続するために必要な情報をまとめています。

**主な内容**:
- プロジェクト概要
- 現在の実装状況
- 今後の開発計画
- 問題生成システムの引継ぎ

**対象読者**: AIアシスタント、開発者

### `user-guides/` - ユーザー向け詳細説明資料

Project Solを使用するユーザー向けの詳細な説明資料です。

**主な内容**:
- セットアップ手順
- APIキーの設定方法
- 動作確認手順
- 問題生成の使い方

**対象読者**: エンドユーザー、運用担当者

### `technical/` - 技術仕様書・設計資料

システムの技術的な詳細を記した資料です。

**主な内容**:
- HyRAG-QGアーキテクチャの設計方針
- 実装レポート（修正内容と実行結果）
- アルゴリズム選定の理論的基盤

**対象読者**: 開発者、技術レビュアー

### `operations/` - 運用マニュアル

システムの運用に関するマニュアルです。

**主な内容**:
- システムアーキテクチャのRoot Definition
- JSON Schema定義
- セキュリティ基準
- 難易度定義
- コンテンツ生成プロセス

**対象読者**: 管理者、運用担当者

## 🚀 クイックリファレンス

### 新規開発を始める場合

1. `ai-handover/00_README.md` - プロジェクト概要を把握
2. `technical/自動問題生成アルゴリズム選定と開発指示.txt` - 設計方針を理解
3. `technical/IMPLEMENTATION_REPORT.md` - 最新の実装状況を確認

### ユーザーとして使用する場合

1. `user-guides/SETUP.md` - セットアップ手順
2. `user-guides/API_KEYS_SETUP.md` - APIキーの設定
3. `user-guides/TESTING_GUIDE.md` - 動作確認

### 運用・管理する場合

1. `operations/PROJECT_MASTER.md` - システム仕様を確認
2. `operations/OPS_MANUAL.md` - 運用マニュアルを参照

## 📚 ドキュメントの優先順位

Project Solでは、以下の優先順位でドキュメントを管理しています：

1. **最優先**: `operations/PROJECT_MASTER.md` - システムのRoot Definition
2. **実装の正**: `operations/PROJECT_MASTER.md` - JSON Schema、セキュリティ基準
3. **設計方針**: `technical/自動問題生成アルゴリズム選定と開発指示.txt`
4. **最新実装**: `technical/IMPLEMENTATION_REPORT.md`

## 🔄 更新履歴

- 2025-01: ディレクトリ整理、IMPLEMENTATION_REPORT追加

