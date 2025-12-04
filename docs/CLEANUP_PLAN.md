# Project Sol: クリーンアップ計画

**作成日**: 2025-12-04  
**目的**: Phase 0完了に伴う不要ファイルの整理

---

## 🔍 調査結果

### 不要なファイル（削除対象）

#### 1. `challenges/drafts/` 内のファイル

**SNSファイル（33個）**:
```
SOL-MSN-*_sns.txt (33ファイル)
```

**JSONファイル（1個）**:
```
SOL-MSN-9PYF.json
```

**これらは全て削除対象**:
- レビュー前の自動生成ファイル
- 品質未確認
- Phase 1で再生成予定

**保持するファイル**:
- `REVIEW_NOTES.md` (新規作成したテンプレート)
- `.gitkeep` (Git管理用)

---

#### 2. `challenges/sqli-01/` ディレクトリ

**内容**:
```
- Dockerfile
- main.py
- requirements.txt
```

**判断**:
- これは手動作成の古いテスト問題
- 新しい自動生成システムとは別物

**オプション**:
- **A: 削除** - クリーンな状態から始める
- **B: サンプルとして保持** - 参考用に残す（推奨しない）
- **C: `samples/` に移動** - サンプルディレクトリに整理

**推奨**: **オプションA（削除）**
- 理由: 自動生成に統一すべき
- 理由: 混乱を避ける

---

## 🔧 削除手順

### ローカル環境での削除

```bash
cd ~/my_ctf_product

# 1. Draftファイルの削除（スクリプト使用）
# すでに cleanup_drafts.sh が存在するので、これで削除可能

# 2. sqli-01 ディレクトリの削除
rm -rf challenges/sqli-01/

# 3. 削除を確認
ls challenges/drafts/
ls challenges/

# 4. Git管理
git add challenges/
git commit -m "chore: Clean up old test challenges and draft files

- Remove challenges/sqli-01/ (old manual test challenge)
- Draft files will be cleaned via cleanup_drafts.sh
- Keep REVIEW_NOTES.md template
- Prepare for Phase 1 content creation"

git push
```

---

### サーバー環境での削除

```bash
cd ~/docker-first-ctf

# 1. 最新コードを取得（ローカルで削除後）
git pull

# 2. Draftファイルのクリーンアップ
./tools/cleanup_drafts.sh
# → "y" を入力

# 3. 確認
ls challenges/drafts/
# REVIEW_NOTES.md だけが残っているはず

ls challenges/
# drafts/ と samples/ だけが残っているはず
```

---

## 📊 削除予定ファイル一覧

### challenges/drafts/

| ファイル | サイズ | 削除理由 |
|---------|--------|----------|
| SOL-MSN-*_sns.txt (33個) | 小 | レビュー前の自動生成 |
| SOL-MSN-9PYF.json (1個) | 中 | 品質未確認 |

**合計**: 約34ファイル

### challenges/sqli-01/

| ファイル | サイズ | 削除理由 |
|---------|--------|----------|
| Dockerfile | 小 | 古い手動作成問題 |
| main.py | 小 | 古い手動作成問題 |
| requirements.txt | 小 | 古い手動作成問題 |

**合計**: 1ディレクトリ（3ファイル）

---

## ✅ 削除後の状態

```
challenges/
├── drafts/
│   ├── .gitkeep
│   └── REVIEW_NOTES.md  ← テンプレート（保持）
└── samples/
    └── valid_mission.json  ← サンプル（保持）
```

**期待される状態**:
- ✅ クリーンな初期状態
- ✅ Phase 1で新規生成を開始可能
- ✅ Git履歴はそのまま保持

---

## 🚨 注意事項

### バックアップ

削除前に、必要に応じてバックアップを取得：

```bash
# ローカルでバックアップ（オプション）
cd ~/my_ctf_product
tar -czf backup_challenges_$(date +%Y%m%d).tar.gz challenges/
```

### Git履歴

- ファイルは削除されるが、Git履歴には残る
- 必要に応じて過去のバージョンから復元可能

```bash
# 過去のファイルを確認
git log -- challenges/sqli-01/

# 復元（必要に応じて）
git checkout <commit-hash> -- challenges/sqli-01/
```

---

## 📝 実行チェックリスト

Phase 0完了作業:

- [ ] ローカル: `challenges/sqli-01/` を削除
- [ ] ローカル: Git コミット・プッシュ
- [ ] サーバー: `git pull`
- [ ] サーバー: `python tools/cli.py reset`
- [ ] サーバー: `./tools/cleanup_drafts.sh`
- [ ] サーバー: `docker system prune -a --volumes -f`
- [ ] サーバー: `docker compose restart`
- [ ] 確認: `ls challenges/drafts/` で REVIEW_NOTES.md のみ
- [ ] 確認: `ls challenges/` で drafts/ と samples/ のみ
- [ ] 確認: `docker ps` で3つのコンテナのみ
- [ ] 確認: `curl http://35.77.44.2:8000/health` で正常応答

---

**完了**: Phase 0クリーンアップ完了、Phase 1開始準備完了

