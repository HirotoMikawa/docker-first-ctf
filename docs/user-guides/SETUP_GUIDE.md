# Project Sol: セットアップガイド（Ver 11.0）

新しいHyRAG-QGアーキテクチャに基づくセットアップ手順です。

## 必要なAPIキーと設定

### 1. Gemini API キー（必須）

**新しいアーキテクチャではGemini 1.5 Flash APIを使用します。**

#### 取得方法

1. **Google AI Studioにアクセス**
   - https://aistudio.google.com/ にアクセス
   - Googleアカウントでログイン

2. **APIキーを取得**
   - 「Get API Key」をクリック
   - 新しいプロジェクトを作成するか、既存のプロジェクトを選択
   - APIキーが生成されます

3. **無料枠の制限**
   - **15 RPM** (1分間に15リクエスト)
   - **1,500 RPD** (1日あたり1,500リクエスト)
   - 個人開発には十分な量です

#### 環境変数の設定

`.env`ファイルに以下を追加:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
USE_GEMINI=true
```

### 2. OpenAI API キー（オプション - レガシー用）

**注意**: 新しいアーキテクチャではGemini APIが推奨されますが、既存のOpenAIベースのコードも動作します。

#### 取得方法

1. **OpenAI Platformにアクセス**
   - https://platform.openai.com/ にアクセス
   - アカウントを作成（クレジットカード登録が必要）

2. **APIキーを取得**
   - 「API Keys」セクションから新しいキーを作成

#### 環境変数の設定

`.env`ファイルに以下を追加（レガシー用）:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Supabase設定（デプロイ用）

問題をデータベースにデプロイする場合に必要です。

#### 取得方法

1. **Supabaseにアクセス**
   - https://supabase.com/ にアクセス
   - アカウントを作成

2. **プロジェクトを作成**
   - 新しいプロジェクトを作成
   - Project URLとService Role Keyを取得

#### 環境変数の設定

`.env`ファイルに以下を追加:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

## 依存パッケージのインストール

### 新しい依存パッケージ

新しいアーキテクチャでは以下のパッケージが必要です:

```bash
cd /home/aniosu/my_ctf_product
pip install -r tools/requirements.txt
```

### 主要な依存パッケージ

- `google-generativeai>=0.8.0` - Gemini API
- `langchain>=0.1.0` - オーケストレーション
- `langchain-community>=0.0.20` - LangChainコミュニティ統合
- `chromadb>=0.4.0` - ベクトルストア（オプション）
- `sentence-transformers>=2.2.0` - ローカル埋め込み（オプション）
- `budoux>=0.9.0` - 日本語テキスト処理（オプション）
- `tenacity>=8.2.0` - リトライロジック
- `pydantic>=2.0.0` - データ検証

### オプション: ローカルLLM（Gemma 2 2B JPN）

インターネット接続がない場合やAPI制限に達した場合のフォールバックとして使用できます。

#### インストール

```bash
pip install llama-cpp-python
```

#### モデルのダウンロード

1. **Hugging Faceからダウンロード**
   - https://huggingface.co/google/gemma-2-2b-jpn-it
   - GGUF形式のモデルをダウンロード

2. **環境変数の設定**

```bash
LOCAL_LLM_PATH=/path/to/gemma-2-2b-jpn-it.gguf
USE_LOCAL_LLM=false  # デフォルトはfalse（APIを使用）
```

## 環境変数ファイルの完全な例

`.env`ファイルの完全な例:

```bash
# Gemini API (必須 - 新しいアーキテクチャ)
GEMINI_API_KEY=your_gemini_api_key_here
USE_GEMINI=true

# OpenAI API (オプション - レガシー用)
OPENAI_API_KEY=your_openai_api_key_here

# Supabase (デプロイ用)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here

# ローカルLLM (オプション)
LOCAL_LLM_PATH=/path/to/gemma-2-2b-jpn-it.gguf
USE_LOCAL_LLM=false

# その他
BASE_URL=https://project-sol.example.com
```

## 動作確認

### 1. APIキーの確認

```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key:
    print('✓ GEMINI_API_KEY is set')
else:
    print('✗ GEMINI_API_KEY is not set')

use_gemini = os.getenv('USE_GEMINI', 'false').lower() == 'true'
if use_gemini:
    print('✓ Using Gemini API (new architecture)')
else:
    print('⚠ Using OpenAI API (legacy)')
"
```

### 2. 依存パッケージの確認

```bash
python3 -c "
try:
    import google.generativeai
    print('✓ google-generativeai is installed')
except ImportError:
    print('✗ google-generativeai is not installed')

try:
    import langchain
    print('✓ langchain is installed')
except ImportError:
    print('✗ langchain is not installed')

try:
    import pydantic
    print('✓ pydantic is installed')
except ImportError:
    print('✗ pydantic is not installed')
"
```

### 3. テスト実行

```bash
cd /home/aniosu/my_ctf_product
python tools/cli.py auto-add --difficulty 3
```

## トラブルシューティング

### Gemini APIのレート制限エラー

**症状**: `429 Too Many Requests`エラー

**解決策**:
- レート制限は自動的に処理されます（4秒間隔）
- 1分間に15リクエストを超えないように注意してください
- バッチ処理を使用してリクエスト数を減らします

### 依存パッケージのインストールエラー

**症状**: `pip install`が失敗する

**解決策**:
```bash
# Python 3.10以上が必要
python3 --version

# 仮想環境を使用
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

pip install --upgrade pip
pip install -r tools/requirements.txt
```

### ChromaDBのエラー

**症状**: ChromaDBの初期化エラー

**解決策**:
- ChromaDBはオプションです
- RAG機能を使用しない場合は、エラーを無視できます
- 必要に応じて`pip install chromadb`を実行

## 次のステップ

1. **APIキーを設定**: `.env`ファイルに`GEMINI_API_KEY`を追加
2. **依存パッケージをインストール**: `pip install -r tools/requirements.txt`
3. **動作確認**: `python tools/cli.py auto-add --difficulty 3`を実行

## 参考資料

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

