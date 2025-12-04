#!/bin/bash
# 
# Project Sol: Draft問題クリーンアップスクリプト
#
# このスクリプトは、生成された問題のDraftファイルとSNSファイルを削除します。
# レビューノートは保持されます。
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DRAFTS_DIR="$PROJECT_ROOT/challenges/drafts"

echo "========================================="
echo "  Project Sol: Draft Cleanup"
echo "========================================="
echo ""

# 確認プロンプト
echo "⚠️  WARNING: This will delete the following files:"
echo "  - All *.json files in challenges/drafts/"
echo "  - All *_sns.txt files in challenges/drafts/"
echo ""
echo "Files that will be KEPT:"
echo "  - REVIEW_NOTES.md"
echo "  - .gitkeep"
echo ""
read -p "Are you sure you want to proceed? [y/N]: " response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "[CLEANUP] Starting draft cleanup..."
echo ""

# JSONファイルの削除
json_count=$(find "$DRAFTS_DIR" -name "*.json" -type f | wc -l)
if [ "$json_count" -gt 0 ]; then
    echo "[DELETE] Removing $json_count JSON file(s)..."
    find "$DRAFTS_DIR" -name "*.json" -type f -delete
    echo "[SUCCESS] Removed $json_count JSON file(s)"
else
    echo "[INFO] No JSON files found"
fi

# SNSファイルの削除
sns_count=$(find "$DRAFTS_DIR" -name "*_sns.txt" -type f | wc -l)
if [ "$sns_count" -gt 0 ]; then
    echo "[DELETE] Removing $sns_count SNS file(s)..."
    find "$DRAFTS_DIR" -name "*_sns.txt" -type f -delete
    echo "[SUCCESS] Removed $sns_count SNS file(s)"
else
    echo "[INFO] No SNS files found"
fi

echo ""
echo "[SUCCESS] Cleanup complete!"
echo ""
echo "Remaining files:"
ls -la "$DRAFTS_DIR"
echo ""

exit 0

