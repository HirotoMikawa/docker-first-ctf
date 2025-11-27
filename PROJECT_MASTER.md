Project Sol: Master Specification (Ver 10.2)

0. Documentation Priority (Single Source of Truth)

このファイルはプロジェクトの Root Definition である。

OPS_MANUAL.md: 安全性・コスト・緊急対応（最優先）

PROJECT_MASTER.md: システムアーキテクチャ・JSON Schema・Security Standards（実装の正）

DIFFICULTY_SPEC.md: 難易度・採点基準の詳細

CONTENT_PLAN.md: 生成プロセス・禁止用語SSOT・パイプライン手順

1. Executive Summary & Vision

Project Name: Docker-First CTF (CodeName: Project_Sol)

Mission: 日本の理系学生・若手エンジニアに対し、インフラ構築・防御・コンテナ技術を「物語（Story）」の中で学べる没入型実践環境を提供する。

Solopreneur Philosophy:

管理者（User）は「AIの手足」となり、意思決定と物理的な実装操作に徹する。

設計段階で例外処理を網羅し、手戻りを極限まで減らす「堅牢なMVP」を目指す。

Core Experience (Narrative):

Role: ユーザーは「セキュリティ機関のエージェント」として参加。

Action: 単なる "Question" ではなく "Mission" を遂行する。

Gamification: UI/UXを通じて没入感を高め、学習の苦痛を取り除く。

2. Technical Architecture & Stack

System Overview

Architecture: Client-Server (REST API)

Isolation: Docker-based Sandboxing per user.

System Components

Frontend: Next.js 14 (App Router), Tailwind CSS, shadcn/ui

Backend: FastAPI (Python 3.11), Docker SDK, slowapi

Database: Supabase (PostgreSQL + Auth)

Infrastructure: VPS (Ubuntu), Docker Engine (Rootless preferred)

Versioning Definition

System Version: 10.2 (本システムのバージョン)

Mission Version: 1.0.0 (SemVer準拠。コンテンツバージョン)

Mission Versioning Rules

MAJOR (x.0.0): 脆弱性タイプの変更、解法ルートの根本的変更（Breaking Change）。

MINOR (0.x.0): ヒント追加、ナラティブ修正、難易度数値の調整。

PATCH (0.0.x): 誤字脱字修正、Metadataの微修正。

API Specification (Core)

GET /health

{
  "status": "ok",
  "system_version": "10.2",
  "dependencies": {
    "database": "connected",
    "docker": "connected"
  },
  "timestamp": "ISO8601_STRING"
}


3. Design System & UI/UX Guidelines (Strict for AI)

AIによるデザインのブレを防ぐため、以下のルールを絶対遵守すること。

A. Visual Theme: "Modern Cyberpunk / Terminal"

Concept: 黒を基調とした、清潔感のあるハッカースタイル。過度な装飾は避け、実用的なダッシュボード（Glassmorphism）を目指す。

UI Library: shadcn/ui (Radix UI + Tailwind CSS) を全面採用する。

Color Palette (Tailwind):

Background: zinc-950 (ほぼ黒)

Card/Surface: zinc-900 with borders zinc-800

Primary Accent: emerald-500 (成功、正常、CUIの文字色)

Destructive: rose-500 (エラー、攻撃検知)

Text: zinc-100 (本文), zinc-400 (補足)

Typography: Headers=Inter, Code=JetBrains Mono.

Feedback: 操作時には必ず視覚的なフィードバック（Toast notification）を行う。

4. Master JSON Schema (SSOT)

全てのAI生成物は、以下の定義に 100% 準拠 すること。

{
  "mission_id": "SOL-MSN-XXX",
  "mission_version": "1.0.0",
  "type": "RCE",
  "difficulty": 3,
  "difficulty_factors": {
    "tech": 3,
    "read": 3,
    "explore": 3
  },
  "vulnerability": {
    "cve_id": "CVE-YYYY-NNNN",
    "cvss": 7.5,
    "attack_vector": "Network"
  },
  "environment": {
    "image": "sol/mission-xxx:latest",
    "base_image": "python:3.11-slim",
    "cost_token": 2500,
    "expected_solve_time": "45m",
    "tags": ["web", "linux"]
  },
  "narrative": {
    "story_hook": "Target system detected at [IP]. Proceed with caution.",
    "tone": "combat"
  },
  "status": "active"
}


Constraints

mission_version: SemVer (MAJOR.MINOR.PATCH).

type: ["RCE", "SQLi", "SSRF", "XXE", "IDOR", "PrivEsc", "LogicError", "Misconfig"]

status: ["draft", "active", "inactive", "deprecated"]

difficulty: Integer (1-5). Must match difficulty_factors calculation.

cost_token: Integer (1000-10000).

expected_solve_time: Regex ^[0-9]+m$ (e.g., "30m", "60m").

narrative:

story_hook: Max 3 sentences. MUST NOT contain Forbidden Words defined in CONTENT_PLAN.md.

tone: Must be "combat".

5. Red-Team Security Standards & Implementation Logic

A. Sandbox Container Rules (User Environment)

Base Image: python:3.11-slim or alpine:3.19.

Expose: 8000/tcp ONLY.

User: ctfuser (UID >= 1000) ONLY. Root prohibited.

Network: ctf_net (Internal) ONLY. No internet access.

Socket: docker.sock Mount PROHIBITED.

Resource Limits:

cpus="0.5" (Anti-Mining).

memory="128m".

pids_limit=50 (Anti-ForkBomb).

B. CI Container Rules (Validation Environment)

Phase 1 (Setup): Root allowed.

Phase 2 (Exploit Verify): Must drop privileges to ctfuser (UID>=1000).

Network: network_mode: none.

Resource Limits: cpus="1.0", memory="256m".

Timeout: Hard limit 120s.

C. Disallowed CVE Types (Prohibited Content)

Kernel-level RCE: ホストOSをクラッシュさせる可能性があるもの。

Privileged Container: --privileged フラグを要求するもの。

Docker Socket Access: ホスト側のDocker操作を要求するもの。

Host Resource Dependency: サンドボックス外のリソース（特定のHW等）に依存するもの。

D. Atomic Startup Strategy (Python Implementation Logic)

コンテナ変数のスコープを管理し、失敗時は確実にクリーンアップを行う。

def start_mission_container(user_id: str, image_name: str):
    container = None
    try:
        # 1. Port 0でコンテナ起動
        container = client.containers.run(
            image=image_name,
            network="ctf_net",
            ports={'8000/tcp': ('0.0.0.0', 0)},
            detach=True,
            # Security constraints
            user="ctfuser",
            mem_limit="128m",
            nano_cpus=500000000, # 0.5 CPU
            pids_limit=50,
            security_opt=["no-new-privileges"]
        )

        # 2. ポート確認
        container.reload()
        assigned_port = container.ports['8000/tcp'][0]['HostPort']

        # 3. DB保存
        # Audit logは常に残すが、失敗時のmission_run一時レコードは作成しない。
        save_to_db(user_id, container.id, assigned_port)
        return {"status": "success", "port": assigned_port}

    except Exception as e:
        # ログ出力 (Observability)
        logger.error(f"Startup failed for user {user_id}: {str(e)}")
        
        # 失敗時は即座にゴミ掃除 (Rollback)
        if container:
            try:
                container.remove(force=True)
            except:
                pass # 削除失敗は無視（Zombie対策はRoutine Cleanupに任せる）
        
        raise HTTPException(500, "Mission Start Failed")


E. Self-Healing Strategy

Startup Cleanup: サーバー起動時に、DB状態と docker ps の乖離を修正（存在しないコンテナのDBレコード削除）。

Routine Cleanup: Cron または APScheduler により、開始から30分経過したコンテナを強制 kill & rm。