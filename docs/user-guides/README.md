# ユーザー向け説明資料

このディレクトリには、Project Solを使用するユーザー向けの詳細な説明資料が含まれています。

## 📁 ファイル一覧

### セットアップ関連

- **SETUP.md**: 基本的なセットアップ手順
- **SETUP_GUIDE.md**: 詳細なセットアップガイド（依存関係、環境変数など）
- **API_KEYS_SETUP.md**: APIキーの取得と設定方法（Gemini API等）

### テスト・検証関連

- **TESTING_GUIDE.md**: 動作確認手順（RAGモード、コンテナ検証など）
- **VERIFICATION_GUIDE.md**: 生成された問題の検証方法

## 🚀 クイックスタート

1. **初回セットアップ**:
   ```bash
   # 1. 依存関係のインストール
   pip install -r requirements-core.txt
   
   # 2. APIキーの設定
   # API_KEYS_SETUP.mdを参照して.envファイルを作成
   
   # 3. 動作確認
   # TESTING_GUIDE.mdを参照
   ```

2. **問題生成**:
   ```bash
   # RAGモード（外部テキストファイルから生成）
   python tools/cli.py auto-add --source inputs/os_command_injection.txt
   
   # 通常モード（ランダムカテゴリ選択）
   python tools/cli.py auto-add
   ```

## 📚 詳細情報

各ファイルの詳細な説明は、各ファイル内の目次を参照してください。

## 🔗 関連資料

- `docs/technical/`: 技術仕様書（開発者向け）
- `docs/operations/`: 運用マニュアル（管理者向け）

