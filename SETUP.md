# 初期セットアップガイド

Ver 5.0c に基づくプロジェクト初期セットアップ手順

## 1. Frontend (/web) セットアップ

### Next.js + Tailwind CSS + shadcn/ui の初期化

```bash
cd web
npm install
```

### shadcn/ui コンポーネントの追加

```bash
# shadcn/ui CLI を使用してコンポーネントを追加
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add dialog
```

### 開発サーバー起動

```bash
npm run dev
```

Frontend は `http://localhost:3000` で起動します。

## 2. Backend (/api) セットアップ

### 仮想環境の作成と依存関係のインストール

```bash
cd api
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 環境変数の設定

`.env.example` を参考に `.env` ファイルを作成：

```bash
# .env ファイルを手動で作成
cat > .env << EOF
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

DOCKER_HOST=unix:///var/run/docker.sock

SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

RATE_LIMIT_PER_MINUTE=5

CONTAINER_TTL_MINUTES=30
CONTAINER_CPU_LIMIT=0.5
CONTAINER_MEMORY_LIMIT=128m
CONTAINER_NETWORK=ctf_net
EOF
```

### 開発サーバー起動

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API は `http://localhost:8000` で起動します。

## 3. Infrastructure セットアップ

### Docker Compose で全体起動

```bash
# プロジェクトルートで実行
docker compose up -d
```

これにより以下が起動します：
- PostgreSQL (ポート 5432)
- Backend API (ポート 8000)
- Frontend (ポート 3000)

### ctf_net ネットワークの確認

Backend起動時に自動的に `ctf_net` (internal network) が作成されます。

手動で確認する場合：

```bash
docker network ls | grep ctf_net
docker network inspect ctf_net
```

## 4. 動作確認

### Backend Health Check

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
```

### Frontend アクセス

ブラウザで `http://localhost:3000` にアクセスし、黒基調UIが表示されることを確認。

### API テスト

```bash
# Mission 一覧取得
curl http://localhost:8000/api/v1/missions

# コンテナ起動（Rate Limit テスト）
curl -X POST http://localhost:8000/api/v1/containers/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "image": "python:3.11-slim", "flag": "flag_test123"}'
```

## 5. 次のステップ

1. **shadcn/ui コンポーネントの追加**: Button, Card, Toast などを追加
2. **Mission Start UI**: Frontend に "Mission Start" ボタンを実装
3. **認証機能**: Supabase Auth の統合
4. **データベーススキーマ**: コンテナ情報、フラグ、ユーザー情報のテーブル定義

## トラブルシューティング

### Docker 接続エラー

```bash
# Docker デーモンが起動しているか確認
docker ps

# Docker socket の権限確認
ls -l /var/run/docker.sock
```

### ポート競合

既に使用されているポートがある場合、`docker-compose.yml` または環境変数で変更してください。

### Rate Limit エラー

5 requests/minute の制限に達した場合、1分待ってから再試行してください。

