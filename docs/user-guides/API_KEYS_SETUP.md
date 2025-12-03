# Project Sol: APIキー設定ガイド

新しいHyRAG-QGアーキテクチャに必要なAPIキーと設定項目の完全なガイドです。

## 📋 目次

1. [必須設定](#必須設定)
2. [オプション設定](#オプション設定)
3. [環境変数ファイルの作成](#環境変数ファイルの作成)
4. [動作確認](#動作確認)

---

## 🔑 必須設定

### 1. Gemini API キー（必須）

**新しいアーキテクチャではGemini 1.5 Flash APIがデフォルトで使用されます。**

#### 取得手順

1. **Google AI Studioにアクセス**
   ```
   https://aistudio.google.com/
   ```
   - Googleアカウントでログイン（無料）

2. **APIキーを取得**
   - 右上の「Get API Key」ボタンをクリック
   - 「Create API Key in new project」または既存のプロジェクトを選択
   - APIキーが生成されます（例: `AIzaSy...`）

3. **無料枠の制限**
   - ✅ **15 RPM** (1分間に15リクエスト)
   - ✅ **1,500 RPD** (1日あたり1,500リクエスト)
   - ✅ 個人開発には十分な量です

#### 環境変数設定

`.env`ファイルに以下を追加:

```bash
GEMINI_API_KEY=AIzaSy...（あなたのAPIキー）
USE_GEMINI=true
```

---

## 🔧 オプション設定

### 2. OpenAI API キー（レガシー用）

**注意**: 新しいアーキテクチャではGemini APIが推奨されますが、既存のOpenAIベースのコードも動作します。

#### 取得手順

1. **OpenAI Platformにアクセス**
   ```
   https://platform.openai.com/
   ```
   - アカウントを作成（クレジットカード登録が必要）

2. **APIキーを取得**
   - 「API Keys」セクションから新しいキーを作成
   - キーは一度しか表示されないので、必ず保存してください

#### 環境変数設定

`.env`ファイルに以下を追加（レガシー用）:

```bash
OPENAI_API_KEY=sk-...（あなたのAPIキー）
```

---

### 3. Supabase設定（デプロイ用）

問題をデータベースにデプロイする場合に必要です。

#### 取得手順

1. **Supabaseにアクセス**
   ```
   https://supabase.com/
   ```
   - アカウントを作成（無料プランあり）

2. **プロジェクトを作成**
   - 「New Project」をクリック
   - プロジェクト名、データベースパスワードを設定
   - リージョンを選択（日本: `ap-northeast-1`）

3. **認証情報を取得**
   - プロジェクトの「Settings」→「API」に移動
   - **Project URL** をコピー（例: `https://xxxxx.supabase.co`）
   - **Service Role Key** をコピー（`eyJ...`で始まる長い文字列）

#### 環境変数設定

`.env`ファイルに以下を追加:

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...（あなたのService Role Key）
```

---

### 4. ローカルLLM（Gemma 2 2B JPN）- オプション

インターネット接続がない場合やAPI制限に達した場合のフォールバックとして使用できます。

#### インストール手順

1. **llama-cpp-pythonをインストール**
   ```bash
   pip install llama-cpp-python
   ```

2. **モデルをダウンロード**
   - Hugging FaceからGGUF形式のモデルをダウンロード:
     ```
     https://huggingface.co/google/gemma-2-2b-jpn-it
     ```
   - `gemma-2-2b-jpn-it-*.gguf` ファイルをダウンロード

3. **環境変数設定**

```bash
LOCAL_LLM_PATH=/path/to/gemma-2-2b-jpn-it.gguf
USE_LOCAL_LLM=false  # デフォルトはfalse（APIを使用）
```

---

## 📝 環境変数ファイルの作成

プロジェクトルート（`/home/aniosu/my_ctf_product/`）に`.env`ファイルを作成します。

### 完全な`.env`ファイルの例

```bash
# ============================================
# Project Sol: 環境変数設定
# ============================================

# ============================================
# Gemini API (必須 - 新しいアーキテクチャ)
# ============================================
GEMINI_API_KEY=AIzaSy...（あなたのAPIキー）
USE_GEMINI=true

# ============================================
# OpenAI API (オプション - レガシー用)
# ============================================
# OPENAI_API_KEY=sk-...（あなたのAPIキー）

# ============================================
# Supabase (デプロイ用)
# ============================================
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...（あなたのService Role Key）

# ============================================
# ローカルLLM (オプション)
# ============================================
# LOCAL_LLM_PATH=/path/to/gemma-2-2b-jpn-it.gguf
# USE_LOCAL_LLM=false

# ============================================
# その他
# ============================================
# BASE_URL=https://project-sol.example.com
```

### `.env`ファイルの作成方法

```bash
cd /home/aniosu/my_ctf_product
nano .env  # または vim .env, code .env
```

上記のテンプレートをコピーして、実際のAPIキーに置き換えてください。

---

## ✅ 動作確認

### 1. APIキーの確認

```bash
cd /home/aniosu/my_ctf_product
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('=' * 70)
print('APIキー設定確認')
print('=' * 70)

# Gemini API
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key:
    print('✓ GEMINI_API_KEY is set')
    print(f'  Key: {gemini_key[:20]}...')
else:
    print('✗ GEMINI_API_KEY is not set (必須)')

# OpenAI API
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print('✓ OPENAI_API_KEY is set (レガシー用)')
else:
    print('⚠ OPENAI_API_KEY is not set (オプション)')

# Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
if supabase_url and supabase_key:
    print('✓ Supabase credentials are set')
else:
    print('⚠ Supabase credentials are not set (デプロイ時に必要)')

# 使用するAPI
use_gemini = os.getenv('USE_GEMINI', 'true').lower() == 'true'
if use_gemini:
    print('✓ Using Gemini API (new architecture)')
else:
    print('⚠ Using OpenAI API (legacy)')

print('=' * 70)
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
    print('  Run: pip install google-generativeai')

try:
    import langchain
    print('✓ langchain is installed')
except ImportError:
    print('✗ langchain is not installed')
    print('  Run: pip install langchain')

try:
    import pydantic
    print('✓ pydantic is installed')
except ImportError:
    print('✗ pydantic is not installed')
    print('  Run: pip install pydantic')
"
```

### 3. テスト実行

```bash
cd /home/aniosu/my_ctf_product
python tools/cli.py auto-add --difficulty 3
```

---

## 🚨 トラブルシューティング

### Gemini APIのレート制限エラー

**症状**: `429 Too Many Requests`エラー

**解決策**:
- レート制限は自動的に処理されます（4秒間隔）
- 1分間に15リクエストを超えないように注意してください
- エラーが続く場合は、少し待ってから再試行してください

### APIキーが認識されない

**症状**: `GEMINI_API_KEY environment variable is required`エラー

**解決策**:
1. `.env`ファイルがプロジェクトルートに存在するか確認
2. `.env`ファイルに`GEMINI_API_KEY=...`が正しく設定されているか確認
3. `python-dotenv`がインストールされているか確認: `pip install python-dotenv`

### 依存パッケージのインストールエラー

**症状**: `pip install`が失敗する

**解決策**:
```bash
# Python 3.10以上が必要
python3 --version

# 仮想環境を使用（推奨）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

pip install --upgrade pip
pip install -r tools/requirements.txt
```

---

## 📚 参考資料

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Google AI Studio](https://aistudio.google.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [LangChain Documentation](https://python.langchain.com/)

---

## 📞 サポート

問題が解決しない場合は、以下を確認してください:

1. `.env`ファイルが正しく設定されているか
2. 依存パッケージがすべてインストールされているか
3. APIキーが有効か（Google AI Studioで確認）
4. インターネット接続が正常か

