Project Sol: Content Production Pipeline (Ver 10.2)

1. Forbidden Words (SSOT)

以下の単語および記号は、Narrative (story_hook, briefing) に含めてはならない。
これは Combat Mode のトーンを維持するためである。

Words: ["Great", "Good luck", "Happy", "Sorry", "Please", "I think", "Feel", "Hope"]

Punctuation: ! (Exclamation mark)

2. Mission Lifecycle Definition

draft: AI生成直後。CI未通過、未レビュー。

active: CI通過、Human Review承認済み、一般公開中。

inactive: バグ発見やコスト調整により一時停止中。ユーザーからは見えない。

deprecated: 技術的に古くなった、または解決不能なバグがあるため廃止。アーカイブ参照のみ可。

3. Production Pipeline Flow

Phase 1: Trend Watch & Filter

Filter: PROJECT_MASTER.md の "Disallowed CVE Types" に該当する脆弱性は除外。

Phase 2: Draft Generation

Mode: COMBAT MODE.

Schema: PROJECT_MASTER.md 準拠。

Constraint: narrative.story_hook にForbidden Wordsを含めないこと。

Phase 3: Auto-Validation (CI)

Environment: Fixed Versions (Python 3.11, Node 18).

Checks:

Build Success.

Security Standards Check.

Exploit Success Rate.

Schema Check (Regex, Ranges).

Forbidden Word Check: story_hook に禁止語が含まれていないか機械的にgrepする。

Phase 4: Human Review

Criteria: Fun Factor, Narrative Fit.

Status Transition: draft -> active.

4. Narrative Style Guide

A. Mission Briefing (Combat Mode)

=== MISSION BRIEFING ===
**Mission ID:** {SOL-MSN-XXX}
**Objective:** {Flag Location}
**Threat Level:** {1-5}

**Intel:**
{Target info - Combat Mode - Max 3 lines}

[COMMAND] Proceed: Y / Abort: N


B. SNS Teaser (Intel Mode)

[MISSION ALERT]
Target: {Target Name} (CVE-XXXX-XXXX)
Level: {Difficulty}/5

Intel suggests a severe vulnerability.
{Sarcastic/Educational commentary}

Dive in: {URL}
#ProjectSol
