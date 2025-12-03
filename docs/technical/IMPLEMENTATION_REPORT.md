# Project Sol: 実装レポート - ファイル永続化とDockerfile生成の改善

## 📋 概要

本レポートは、Project Solの`auto-add`コマンドにおける「ファイル永続化問題」と「Dockerfile生成の不整合」を解決するための修正内容と実行結果をまとめたものです。

**作成日**: 2025年1月  
**対象バージョン**: Project Sol Ver 11.0+  
**関連資料**: `tools/自動問題生成アルゴリズム選定と開発指示.txt`

---

## 🎯 修正の背景と目的

### 問題の特定

1. **ファイル欠損問題**: 生成された`app.py`が`/flag.txt`や`database.db`を参照しているにもかかわらず、Dockerコンテナ内にこれらのファイルが存在しない
2. **Dockerfile順序問題**: `COPY`コマンドが`WORKDIR`より前に実行され、相対パスが正しく解決されない
3. **フラグ配置の不整合**: RCE問題とWeb問題でフラグの配置場所が統一されていない

### 作成方針との整合性

`tools/自動問題生成アルゴリズム選定と開発指示.txt`では、以下の方針が示されています：

- **HyRAG-QGアーキテクチャ**: Gemini APIを主軸とした問題生成
- **構造化出力**: Pydanticによる厳密な型定義
- **品質保証**: LLM-as-a-Judgeによる自動評価
- **コスト最適化**: 無料枠の徹底活用

今回の修正は、特に「品質保証」と「構造化出力」の観点から、生成された問題が確実に動作することを保証するためのものです。

---

## 🔧 実装した修正内容

### 1. FILE PERSISTENCE RULEの実装

#### 1.1 System Promptへの追加

**ファイル**: `tools/generation/gemini_drafter.py`

```python
# [CRITICAL: FILE PERSISTENCE RULE - HIGHEST PRIORITY]
file_persistence_rule = """
[CRITICAL: FILE PERSISTENCE RULE - HIGHEST PRIORITY]

If your challenge scenario involves reading a file (e.g., "/flag.txt", "/app/config.php", "/home/ctfuser/flag.txt", "database.db"), you MUST ensure this file is created in the Dockerfile.

**Requirement:**
1. **File Creation in Dockerfile**: In the `Dockerfile` content you generate, use `RUN` commands to create ALL files that are referenced in `app.py`.
   - BAD: Assuming the file exists.
   - GOOD: `RUN echo "SolCTF{...}" > /flag.txt && chmod 644 /flag.txt`
   - GOOD: `RUN sqlite3 database.db < init.sql` (for database files)

2. **Path Consistency**: The path in `app.py` (e.g., `open("/flag.txt")`, `cat /flag.txt`) MUST match the path in `Dockerfile` (e.g., `RUN echo ... > /flag.txt`).
   - If `app.py` reads `/flag.txt`, then Dockerfile MUST create `/flag.txt`.
   - If `app.py` reads `/home/ctfuser/flag.txt`, then Dockerfile MUST create `/home/ctfuser/flag.txt`.
   - If `app.py` reads `database.db`, then Dockerfile MUST create `database.db` with proper initialization.

3. **Permissions**: Ensure the `ctfuser` can read the flag file.
   - Use `chmod 644` or `chown ctfuser:ctfuser`.
   - Correct order: 1) FROM, 2) RUN useradd/adduser, 3) **RUN echo ... > file.txt (create files)**, 4) COPY files, 5) RUN pip install, 6) USER ctfuser, 7) WORKDIR, 8) EXPOSE, 9) CMD

4. **Database Files**: If `app.py` uses SQLite (`database.db`), you MUST initialize it in Dockerfile:
   ```dockerfile
   RUN sqlite3 database.db "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT);"
   RUN sqlite3 database.db "INSERT INTO users VALUES (1, 'admin', 'password123');"
   ```

5. **The `files` JSON object MUST include "app.py", "Dockerfile", and any other required files.**

6. **DO NOT assume files exist. CREATE THEM in the Dockerfile.**

Before submitting your Dockerfile, verify:
- [ ] Every file referenced in `app.py` (via `open()`, `cat`, `sqlite3`, etc.) is created in Dockerfile
- [ ] File paths in `app.py` match file paths in Dockerfile exactly
- [ ] Permissions are set correctly for `ctfuser`
"""
```

#### 1.2 効果

- AIが生成するDockerfileに、`app.py`で参照されるすべてのファイルを作成する`RUN`コマンドが含まれるようになった
- ファイルパスの不整合が大幅に減少

---

### 2. WORKDIR/COPY順序の問題修正

#### 2.1 問題の詳細

**エラー例**:
```
python: can't open file '/home/ctfuser/app.py': [Errno 2] No such file or directory
```

**原因**: Dockerfileの順序が不適切
```dockerfile
COPY app.py requirements.txt ./    # WORKDIR未設定 → /にコピーされる
WORKDIR /home/ctfuser              # その後、WORKDIRを変更
CMD ["python", "app.py"]           # /home/ctfuserからapp.pyを探すが、/にある
```

#### 2.2 System Promptへの注意追加

**ファイル**: `tools/generation/gemini_drafter.py`

```python
**WORKDIRとCOPYの順序（CRITICAL）:**
- ❌ `COPY app.py ./` → `WORKDIR /home/ctfuser` → `CMD ["python", "app.py"]` (エラー: app.pyが見つからない)
- ✅ `WORKDIR /home/ctfuser` → `COPY app.py ./` → `CMD ["python", "app.py"]` (正しい)
- または: `COPY app.py /home/ctfuser/` → `WORKDIR /home/ctfuser` → `CMD ["python", "app.py"]` (正しい)
- **重要**: COPYの前にWORKDIRを設定するか、COPYの宛先を絶対パスで指定すること
```

#### 2.3 自動修正ロジックの実装

**ファイル**: `tools/builder/simple_builder.py`

```python
# Fix COPY command syntax and WORKDIR/COPY order
import re
lines = dockerfile_content.split('\n')

# First pass: Find WORKDIR and COPY positions
workdir_line_idx = None
workdir_path = None
copy_line_indices = []

for i, line in enumerate(lines):
    if line.strip().startswith('WORKDIR'):
        workdir_line_idx = i
        workdir_path = line.strip().split(' ', 1)[1] if ' ' in line.strip() else None
    elif line.strip().startswith('COPY'):
        copy_line_indices.append(i)

# Second pass: Fix issues
fixed_lines = []
for i, line in enumerate(lines):
    # Fix COPY command syntax (multiple files must end with /)
    if line.strip().startswith('COPY') and ' ' in line:
        parts = line.split()
        if len(parts) >= 4:  # COPY file1 file2 ... dest
            dest = parts[-1]
            # Fix: COPY with relative path before WORKDIR
            if (workdir_line_idx is None or i < workdir_line_idx) and (dest == '.' or dest == './'):
                # COPY is before WORKDIR - change to absolute path or add WORKDIR before
                target_dir = workdir_path if workdir_path else '/app'
                fixed_line = line.rsplit(' ', 1)[0] + ' ' + target_dir + '/'
                fixed_lines.append(fixed_line)
                corrections_applied.append("COPY path (before WORKDIR)")
                continue
    fixed_lines.append(line)

# Third pass: Ensure WORKDIR is set before COPY with relative paths
if workdir_line_idx is not None and copy_line_indices:
    first_copy_idx = min(copy_line_indices)
    if workdir_line_idx > first_copy_idx:
        # WORKDIR comes after first COPY - need to check if COPY uses relative path
        needs_fix = False
        for copy_idx in copy_line_indices:
            if copy_idx < workdir_line_idx:
                copy_line = fixed_lines[copy_idx]
                if ' ./' in copy_line or copy_line.strip().endswith(' .'):
                    needs_fix = True
                    break
        
        if needs_fix:
            # Move WORKDIR before first COPY
            workdir_line = fixed_lines[workdir_line_idx]
            fixed_lines.pop(workdir_line_idx)
            insert_idx = min(copy_line_indices)
            fixed_lines.insert(insert_idx, workdir_line)
            corrections_applied.append("WORKDIR order")

dockerfile_content = '\n'.join(fixed_lines)
```

#### 2.4 効果

- `COPY`が`WORKDIR`より前で相対パスを使っている場合、自動的に絶対パスに変換
- または、`WORKDIR`を`COPY`の前に移動
- コンテナ起動時の「ファイルが見つからない」エラーが解消

---

### 3. フラグ配置の標準化

#### 3.1 FLAG PLACEMENT STANDARDSの追加

**ファイル**: `tools/generation/gemini_drafter.py`

```python
**[CRITICAL: FLAG PLACEMENT STANDARDS]**

You MUST follow these strict rules for placing the flag "SolCTF{...}".

1. **Category: RCE / LFI / Linux Misc**
   - **Method:** FILE
   - **Requirement:** You MUST create a flag file at `/home/ctfuser/flag.txt`.
   - **Dockerfile Instruction:** `RUN echo "SolCTF{RANDOM_STRING}" > /home/ctfuser/flag.txt && chmod 644 /home/ctfuser/flag.txt`
   - **Writeup:** Explain that the user needs to read `/home/ctfuser/flag.txt`.

2. **Category: Web (SQLi / XSS / SSRF)**
   - **Method:** ENVIRONMENT VARIABLE (Primary) & FILE (Backup)
   - **Requirement:** Set the flag as an environment variable AND a file.
   - **Dockerfile Instruction:** 
     ```dockerfile
     ENV FLAG="SolCTF{RANDOM_STRING}"
     RUN echo "SolCTF{RANDOM_STRING}" > /flag.txt
     ```
   - **App Code:** The app typically reads from `os.getenv('FLAG')` or a database initialized with this value.
```

#### 3.2 効果

- RCE問題とWeb問題でフラグの配置場所が統一された
- 内部検査（`docker exec`）による検証が容易になった

---

### 4. RAG統合（簡易版）

#### 4.1 `--source`オプションの追加

**ファイル**: `tools/cli.py`

```python
@cli.command()
@click.option('--source', '-s', type=click.Path(exists=True), 
              help='外部テキストファイルを読み込んでRAG生成に使用')
def cmd_auto_add(source: Optional[str] = None):
    """自動問題生成コマンド（RAG対応）"""
    # ...
    source_text = None
    if source:
        with open(source, 'r', encoding='utf-8') as f:
            source_text = f.read()
        print(f"[INFO] Loaded source text from: {source} ({len(source_text)} characters)")
    
    # drafterにsource_textを渡す
    draft_result = drafter.draft(source_text=source_text)
```

#### 4.2 プロンプトへの統合

**ファイル**: `tools/generation/gemini_drafter.py`

```python
def _build_user_prompt(self, source_text: Optional[str] = None, ...) -> str:
    if source_text:
        prompt = f"""以下の技術解説テキストを基に、CTF問題を生成してください。

【ソーステキスト】
{source_text}

【要件】
1. 上記のテキストに記載されている脆弱性を再現するPythonコード（Flaskなど）を作成してください。
2. フラグは `SolCTF{{...}}` 形式で、適切な場所に配置してください。
3. 攻略法（Writeup）はMarkdown形式で、具体的な攻撃手順を記述してください。
...
"""
    else:
        # 従来のランダムカテゴリ選択ロジック
        ...
```

#### 4.3 効果

- 外部テキストファイル（解説記事など）を基に問題を生成できるようになった
- 将来的な完全版RAG（ChromaDB + ベクトル検索）への移行が容易

---

## 📊 実行結果と検証

### テストケース: OS Command Injection問題

**コマンド**:
```bash
python tools/cli.py auto-add --source inputs/os_command_injection.txt
```

**生成結果**:
- Mission ID: `SOL-MSN-HBLW`
- Dockerイメージ: `sol/mission-hblw:latest`
- フラグ: `SolCTF{command_injection_secured}`

**生成されたDockerfile**:
```dockerfile
FROM python:3.11-slim

RUN useradd -m -u 1000 ctfuser

RUN apt-get update && apt-get install -y --no-install-recommends netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

RUN echo "SolCTF{command_injection_secured}" > /home/ctfuser/flag.txt && chmod 644 /home/ctfuser/flag.txt

WORKDIR /app

COPY app.py requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

USER ctfuser

EXPOSE 8000

CMD ["python", "app.py"]
```

**検証結果**:
- ✅ Dockerイメージのビルド成功
- ✅ コンテナ起動成功（Flaskアプリが正常に動作）
- ✅ フラグファイルの存在確認: `/home/ctfuser/flag.txt`に存在
- ✅ RCE機能の動作確認: POSTリクエストでコマンド実行が可能
- ✅ フラグ取得の確認: `cat /home/ctfuser/flag.txt`でフラグを取得可能

---

## 🎯 作成方針との整合性チェック

### ✅ HyRAG-QGアーキテクチャ

- **Gemini APIの使用**: ✅ `GeminiMissionDrafter`でGemini 2.0 Flashを使用
- **構造化出力**: ✅ Pydanticモデル（`CTFMission`）による厳密な型定義
- **RAG統合**: ✅ 簡易版RAG（直接プロンプト埋め込み）を実装

### ✅ 品質保証

- **FILE PERSISTENCE RULE**: ✅ System Promptに最優先事項として追加
- **自動修正ロジック**: ✅ `simple_builder.py`でDockerfileの不整合を自動修正
- **内部検査**: ✅ `container_tester.py`で`docker exec`によるフラグ検証

### ✅ コスト最適化

- **無料枠の活用**: ✅ Gemini 2.0 Flashの無料枠を使用
- **ローカル処理**: ✅ Dockerfileの修正はローカルで実行（APIコストなし）

---

## 📝 今後の改善点

1. **完全版RAGの実装**:
   - ChromaDBを使ったベクトル検索の統合
   - 複数ソースファイルからの関連情報の抽出

2. **LLM-as-a-Judgeの実装**:
   - 生成された問題の品質を自動評価
   - 基準を満たさない問題の自動再生成

3. **エラーハンドリングの強化**:
   - Dockerfile生成失敗時の詳細なエラーメッセージ
   - 自動修正が適用された場合のログ出力

---

## 📚 関連ファイル

- `tools/generation/gemini_drafter.py`: System PromptとRAG統合
- `tools/builder/simple_builder.py`: Dockerfile自動修正ロジック
- `tools/cli.py`: `--source`オプションの実装
- `tools/solver/container_tester.py`: 内部検査による検証

---

**作成者**: AI Assistant (Cursor)  
**レビュー**: ユーザー確認済み  
**次回更新**: 完全版RAG実装時

