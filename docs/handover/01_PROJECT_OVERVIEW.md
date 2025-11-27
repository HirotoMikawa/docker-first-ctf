# Project Sol: プロジェクト概要（引継ぎ資料）

## プロジェクト基本情報

**プロジェクト名:** Project Sol (CodeName: Project_Sol)  
**現在のバージョン:** Ver 10.2 (Production Ready)  
**前バージョン:** Ver 5.0c (Prototype)  
**最終更新日:** 2025年1月

## プロジェクトのミッション

日本の理系学生・若手エンジニアに対し、インフラ構築・防御・コンテナ技術を「物語（Story）」の中で学べる没入型実践環境を提供する。

### コアコンセプト

- **Role:** ユーザーは「セキュリティ機関のエージェント」として参加
- **Action:** 単なる "Question" ではなく "Mission" を遂行する
- **Gamification:** UI/UXを通じて没入感を高め、学習の苦痛を取り除く

### Solopreneur Philosophy

- 管理者（User）は「AIの手足」となり、意思決定と物理的な実装操作に徹する
- 設計段階で例外処理を網羅し、手戻りを極限まで減らす「堅牢なMVP」を目指す

## 技術スタック

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui (Radix UI + Tailwind CSS)
- **Authentication:** Supabase Auth (JWT)

### Backend
- **Framework:** FastAPI (Python 3.11)
- **Container Management:** Docker SDK
- **Rate Limiting:** slowapi
- **Validation:** Pydantic v2

### Infrastructure
- **Database:** Supabase (PostgreSQL + Auth)
- **Container Runtime:** Docker Engine (Rootless preferred)
- **Deployment:** VPS (Ubuntu), Docker Compose
- **Network:** Docker Internal Network (`ctf_net`)

## システムアーキテクチャ

```
┌─────────────┐
│   Frontend  │  Next.js (Port 3000)
│  (Next.js)  │
└──────┬──────┘
       │ REST API
       │ (JWT Auth)
┌──────▼──────┐
│   Backend   │  FastAPI (Port 8000)
│  (FastAPI)  │
└──────┬──────┘
       │
       ├──► Supabase (PostgreSQL + Auth)
       │
       └──► Docker Engine
            │
            └──► Challenge Containers (Isolated)
                 - Network: ctf_net (Internal)
                 - User: ctfuser (Non-root)
                 - Resource Limits: CPU 0.5, Memory 128m, PIDs 50
```

## セキュリティアーキテクチャ

### サンドボックスコンテナルール（ユーザー環境）

- **Base Image:** python:3.11-slim または alpine:3.19
- **Expose:** 8000/tcp ONLY
- **User:** ctfuser (UID >= 1000) ONLY. Root禁止
- **Network:** ctf_net (Internal) ONLY. インターネットアクセス不可
- **Socket:** docker.sock Mount 禁止
- **Resource Limits:**
  - CPU: 0.5 (Anti-Mining)
  - Memory: 128m
  - PIDs: 50 (Anti-ForkBomb)

### 禁止されているCVEタイプ

- Kernel-level RCE（ホストOSをクラッシュさせる可能性）
- Privileged Container（--privileged フラグを要求）
- Docker Socket Access（ホスト側のDocker操作を要求）
- Host Resource Dependency（サンドボックス外のリソースに依存）

## バージョニング定義

### System Version
- **現在:** 10.2 (本システムのバージョン)

### Mission Version
- **形式:** SemVer (MAJOR.MINOR.PATCH)
- **例:** 1.0.0
- **ルール:**
  - MAJOR (x.0.0): 脆弱性タイプの変更、解法ルートの根本的変更（Breaking Change）
  - MINOR (0.x.0): ヒント追加、ナラティブ修正、難易度数値の調整
  - PATCH (0.0.x): 誤字脱字修正、Metadataの微修正

## デザインシステム

### Visual Theme: "Modern Cyberpunk / Terminal"

- **Background:** zinc-950 (ほぼ黒)
- **Card/Surface:** zinc-900 with borders zinc-800
- **Primary Accent:** emerald-500 (成功、正常、CUIの文字色)
- **Destructive:** rose-500 (エラー、攻撃検知)
- **Text:** zinc-100 (本文), zinc-400 (補足)
- **Typography:** Headers=Inter, Code=JetBrains Mono

### UI Library
- shadcn/ui (Radix UI + Tailwind CSS) を全面採用

---

**次のドキュメント:** [02_CURRENT_STATUS.md](./02_CURRENT_STATUS.md)

