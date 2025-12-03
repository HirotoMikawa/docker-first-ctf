Project Sol: Operations Manual (Ver 10.2)

1. Service Standards (SLA)

MTTA: 5 min.

MTTR: 15 min.

2. Health Check Specification

Backend API /health を監視する。

Expected Response: {"status": "ok", "system_version": "10.2", ...}

Condition: DB接続およびDocker Engine接続が正常であること。

3. Pipeline State Machine (Cost Control)

コスト制御基準は本ドキュメントを正とする。

State: NORMAL

Condition: Monthly Cost <= ¥2,999

Behavior: Full Operation.

State: STOP (Level 1)

Range: ¥3,000 <= Monthly Cost <= ¥4,999

Reset Condition: Monthly Cost <= ¥2,999 (Typically next month start).

Action: Draft Generation 停止。

Notification: [Cost Alert L1] Pipeline STOP.

State: THROTTLED (Level 2)

Range: ¥5,000 <= Monthly Cost <= ¥6,999

Reset Condition: Monthly Cost <= ¥4,999.

Action: CI Concurrency = 1. New containers blocked.

Notification: [Cost Alert L2] Maintenance Mode.

State: FROZEN (Level 3)

Range: Monthly Cost >= ¥7,000

Reset Condition: Monthly Cost <= ¥6,999 (Manual intervention required to unfreeze API).

Action: API_READ_ONLY=True. Containers Stopped.

Notification: [Cost Alert L3] System Frozen.

4. Routine Operations

Daily: SNS Post (Intel Mode).

Weekly: New Mission Release.

Monthly: Cost Reset & Review.