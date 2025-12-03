Project Sol: Setup Guide (Ver 10.2)

1. Frontend Setup (/web)

Next.js + Tailwind + shadcn/ui 環境の構築。

ディレクトリ移動: cd web

依存インストール: npm install

UIコンポーネント追加: npx shadcn-ui@latest add button card toast dialog

開発起動:

ローカル開発: npm run dev (http://localhost:3000)

本番デプロイ: Build & Start (http://<SERVER_IP>:3000)

2. Backend Setup (/api)

FastAPI + Docker SDK 環境の構築。

ディレクトリ移動: cd api

仮想環境作成: python -m venv venv

仮想環境有効化: source venv/bin/activate (Win: venv\Scripts\activate)

依存インストール: pip install -r requirements.txt

環境変数設定: .env ファイルを作成

API_HOST=0.0.0.0

CONTAINER_CPU_LIMIT=0.5

CONTAINER_MEMORY_LIMIT=128m

CONTAINER_PIDS_LIMIT=50

開発起動: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

3. Infrastructure Setup

Docker Compose による全体統合。

ルートディレクトリで実行: docker compose up -d

ネットワーク確認: docker network ls | grep ctf_net が存在すること。

4. Verification

正常動作の確認手順。

Health Check: curl http://<SERVER_IP>:8000/health -> {"status": "ok", "system_version": "10.2", ...}

Container Launch:
curl -X POST http://<SERVER_IP>:8000/api/v1/containers/start ...
エラーなくポートが返却されれば成功。

5. Observability Setup (New)

本番運用時の監視設定。

Log Rotation: Dockerのログ肥大化を防ぐ。
/etc/docker/daemon.json:

{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}


Health Monitoring: 5分おきに /health を叩く Cron または Uptime Robot を設定する。

6. AI Assistant Setup

プロジェクトルートに .cursorrules を配置し、Cursor エディタに再読み込みさせる。