Project Sol: Difficulty Specification (Ver 10.2)

1. Difficulty Formula

Difficulty = Clamp(Round(Tech * 0.4 + Read * 0.2 + Explore * 0.4), 1, 5)

2. Factor Range Definition

各 Factor は必ず 1 から 5 の整数 でなければならない。

3. Consistency Rules

Difficulty 1: Tech <= 2, Explore <= 2

Difficulty 2: Tech 2-3, Explore 2-3 (Bridge level)

Difficulty 3: Tech 3-4, Explore 3-4

Difficulty 4: Tech 4, Explore 4 (High Bridge)

Difficulty 5: Tech >= 4, Explore >= 4

4. Exploit Success Thresholds (Validation)

Diff 1-2: 3/3 Success (100%)

Diff 3-4: 2/3 Success (>66%)

Diff 5: 1/3 Success (>33%)

5. Scoring Criteria (Rubric)

A. Technical Complexity (Tech)

Level 1: 平文情報の検索 (grep, find)。

Level 3: フィルタ回避が必要な Web/OS Cmd Injection。

Level 5 (Advanced Sandbox-Safe):

Kernel/Host攻撃は禁止。

Race Condition (TOCTOU): ファイル書き込みと読み込みの隙間を突く。

Complex Serialization: 複数のGadget Chainを組み合わせる。

Blind SQLi with Time-Delay: 応答差分のみでデータを抜く。

B. Readability / Volume (Read)

Level 1: ソースコードなし、または短い設定ファイルのみ。

Level 3: 小規模なWebアプリソースコード (Python/PHP)。

Level 5: 難読化されたコード、または大規模フレームワークの解析。

C. Exploration Steps (Explore)

Level 1: 初期アクセス地点にフラグが存在。

Level 3: 横展開 (Lateral Movement) または 権限昇格 (PrivEsc) が1回必要。

Level 5 (Internal Pivot):

Hostへの脱出は禁止。

Multi-stage: Webアプリ攻略 -> 内部RedisへのSSRF -> RCE発動。

Logic Chain: 複数の脆弱性を特定順序で発火させる必要がある。