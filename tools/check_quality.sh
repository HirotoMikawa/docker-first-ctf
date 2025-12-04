#!/bin/bash
#
# Project Sol: 問題品質自動チェックスクリプト
#
# 使用方法:
#   ./tools/check_quality.sh challenges/drafts/SOL-MSN-XXXX.json
#

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <mission_json_file>"
    exit 1
fi

MISSION_JSON=$1

if [ ! -f "$MISSION_JSON" ]; then
    echo "Error: File not found: $MISSION_JSON"
    exit 1
fi

echo "========================================="
echo "  Quality Check: $(basename $MISSION_JSON)"
echo "========================================="
echo ""

# jqがインストールされているか確認
if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed. Install with: sudo apt install jq"
    exit 1
fi

PASSED=0
FAILED=0
WARNINGS=0

# チェック1: /flag エンドポイントの検出
echo "[CHECK 1/5] Checking for debug endpoints..."
if jq -r '.files."app.py"' "$MISSION_JSON" | grep -q "@app.route('/flag')"; then
    echo "  ❌ FAILED: /flag endpoint detected (直接フラグを返すエンドポイント)"
    ((FAILED++))
else
    echo "  ✅ PASSED: No /flag endpoint"
    ((PASSED++))
fi

# チェック2: /debug, /admin エンドポイントの検出
if jq -r '.files."app.py"' "$MISSION_JSON" | grep -qE "@app.route('/(debug|admin)"; then
    echo "  ⚠️  WARNING: /debug or /admin endpoint detected"
    ((WARNINGS++))
fi

# チェック3: shell=False の検出（RCE問題の場合）
echo "[CHECK 2/5] Checking vulnerability implementation..."
PROBLEM_TYPE=$(jq -r '.type' "$MISSION_JSON")

if [ "$PROBLEM_TYPE" = "RCE" ] || echo "$PROBLEM_TYPE" | grep -qi "command"; then
    if jq -r '.files."app.py"' "$MISSION_JSON" | grep -q "shell=False"; then
        echo "  ❌ FAILED: shell=False detected in RCE/Command Injection challenge"
        echo "     脆弱性が動作しません！"
        ((FAILED++))
    else
        echo "  ✅ PASSED: shell=True or shell parameter not restricted"
        ((PASSED++))
    fi
else
    echo "  ⏭️  SKIPPED: Not an RCE challenge"
fi

# チェック4: Prepared statement の検出（SQLi問題の場合）
echo "[CHECK 3/5] Checking SQL injection implementation..."
if [ "$PROBLEM_TYPE" = "SQLi" ] || echo "$PROBLEM_TYPE" | grep -qi "sql"; then
    if jq -r '.files."app.py"' "$MISSION_JSON" | grep -qE "execute.*\?|execute.*%s"; then
        echo "  ⚠️  WARNING: Possible prepared statement or parameterized query detected"
        echo "     SQLインジェクションが防がれている可能性があります"
        ((WARNINGS++))
    else
        echo "  ✅ PASSED: No prepared statements detected (string concatenation likely used)"
        ((PASSED++))
    fi
else
    echo "  ⏭️  SKIPPED: Not a SQLi challenge"
fi

# チェック5: フラグファイルの存在確認
echo "[CHECK 4/5] Checking flag file creation..."
if jq -r '.files.Dockerfile' "$MISSION_JSON" | grep -q "echo.*SolCTF.*>.*flag.txt"; then
    echo "  ✅ PASSED: Flag file creation found in Dockerfile"
    ((PASSED++))
else
    echo "  ⚠️  WARNING: Flag file creation not found in Dockerfile"
    ((WARNINGS++))
fi

# チェック6: 必須フィールドの確認
echo "[CHECK 5/5] Checking required fields..."
REQUIRED_FIELDS=("mission_id" "type" "difficulty" "flag_answer" "writeup")
ALL_FIELDS_OK=true

for field in "${REQUIRED_FIELDS[@]}"; do
    if ! jq -e ".$field" "$MISSION_JSON" > /dev/null 2>&1; then
        echo "  ❌ FAILED: Missing required field: $field"
        ((FAILED++))
        ALL_FIELDS_OK=false
    fi
done

if [ "$ALL_FIELDS_OK" = true ]; then
    echo "  ✅ PASSED: All required fields present"
    ((PASSED++))
fi

# 結果サマリー
echo ""
echo "========================================="
echo "  Quality Check Summary"
echo "========================================="
echo "  ✅ Passed: $PASSED"
echo "  ❌ Failed: $FAILED"
echo "  ⚠️  Warnings: $WARNINGS"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ Overall: PASSED"
    if [ $WARNINGS -gt 0 ]; then
        echo "   ($WARNINGS warning(s) - please review manually)"
    fi
    exit 0
else
    echo "❌ Overall: FAILED ($FAILED critical issue(s))"
    echo ""
    echo "推奨: この問題は却下し、再生成してください"
    exit 1
fi

