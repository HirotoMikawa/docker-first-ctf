# Black Market Shop: Logic Error & Integer Overflow

## シナリオ

あなたは、Afterlife Marketplace のセキュリティ監査員として、闇市のオンラインショップシステムの脆弱性診断を実施している。

**ターゲット**: 地下マーケットのアイテム購入システム  
**目的**: ビジネスロジックの欠陥を突き、本来購入できない高額アイテムを入手せよ  
**インテル**: このショップは、ユーザーに初期クレジット（1000円）を付与し、アイテムを購入させる仕組みだが、数量や価格の計算に論理的な欠陥がある可能性がある。特に、マイナス数量の処理や、整数オーバーフローの可能性が指摘されている。あなたの任務は、これらの欠陥を悪用して高額な「Flag Item」（価格: 1,000,000円）を購入し、フラグを入手することだ。

**ミッション**: ロジックエラーを利用し、クレジットを操作して高額アイテムを購入せよ。

---

## 技術的背景: Logic Error（ビジネスロジックの脆弱性）

### 概要

**Logic Error** は、アプリケーションのビジネスロジック（計算、検証、状態管理等）に欠陥があり、意図しない動作を引き起こす脆弱性です。

### よくあるパターン

1. **マイナス数量**:
   ```python
   quantity = -1
   total = price * quantity  # -100円（クレジット増加）
   ```

2. **整数オーバーフロー**:
   ```python
   quantity = 999999999
   total = price * quantity  # オーバーフローして負の数に
   ```

3. **Race Condition**:
   ```python
   # 同時に2回購入 → 在庫チェックがバイパスされる
   ```

4. **価格改ざん**:
   ```python
   # フロントエンドから送信される価格を信頼してしまう
   ```

---

## 脆弱なコードの仕様

### アプリケーション構成

**技術スタック**:
- **言語**: Python 3.11
- **フレームワーク**: Flask 3.0.0
- **セッション**: Flask session
- **ポート**: 8000

### 商品リスト

```python
ITEMS = {
    1: {"name": "Common Part", "price": 100},
    2: {"name": "Rare Component", "price": 500},
    3: {"name": "Epic Weapon", "price": 2000},
    99: {"name": "FLAG ITEM - Classified Data", "price": 1000000}
}
```

### 脆弱なコード実装

```python
from flask import Flask, request, render_template_string, session, redirect
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

ITEMS = {
    1: {"name": "Common Part", "price": 100},
    2: {"name": "Rare Component", "price": 500},
    3: {"name": "Epic Weapon", "price": 2000},
    99: {"name": "FLAG ITEM - Classified Data", "price": 1000000}
}

@app.route('/')
def index():
    # 初期クレジット
    if 'credit' not in session:
        session['credit'] = 1000
    
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>ロジックエラー - ショップ</title>
            <style>
                body {
                    background: #0a0a0a;
                    color: #ffaa00;
                    font-family: monospace;
                    padding: 20px;
                }
                .shop {
                    max-width: 800px;
                    margin: 0 auto;
                    border: 2px solid #ffaa00;
                    padding: 20px;
                }
                .item {
                    border: 1px solid #666;
                    padding: 10px;
                    margin: 10px 0;
                }
                .expensive {
                    border-color: #ff0080;
                    background: #1a0a0a;
                }
                input[type="number"] {
                    width: 60px;
                    background: #1a1a1a;
                    color: #ffaa00;
                    border: 1px solid #ffaa00;
                    padding: 5px;
                }
                button {
                    background: #ffaa00;
                    color: #0a0a0a;
                    border: none;
                    padding: 5px 10px;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <div class="shop">
                <h1>AFTERLIFE MARKETPLACE</h1>
                <h2>Black Market Shop</h2>
                <h3>[UNDERGROUND ACCESS]</h3>
                <hr>
                <p><b>Your Credit:</b> {{ credit }} 円</p>
                <hr>
                <h3>商品一覧:</h3>
                
                <div class="item">
                    <p><b>#1 Common Part</b> - 100円</p>
                    <form method="post" action="/buy" style="display:inline;">
                        <input type="hidden" name="item_id" value="1">
                        <input type="number" name="quantity" value="1" min="1">
                        <button type="submit">Purchase</button>
                    </form>
                </div>
                
                <div class="item">
                    <p><b>#2 Rare Component</b> - 500円</p>
                    <form method="post" action="/buy" style="display:inline;">
                        <input type="hidden" name="item_id" value="2">
                        <input type="number" name="quantity" value="1" min="1">
                        <button type="submit">Purchase</button>
                    </form>
                </div>
                
                <div class="item">
                    <p><b>#3 Epic Weapon</b> - 2000円</p>
                    <form method="post" action="/buy" style="display:inline;">
                        <input type="hidden" name="item_id" value="3">
                        <input type="number" name="quantity" value="1" min="1">
                        <button type="submit">Purchase</button>
                    </form>
                </div>
                
                <div class="item expensive">
                    <p><b>#99 FLAG ITEM - Classified Data</b> - <span style="color:#f00;">1,000,000円</span></p>
                    <form method="post" action="/buy" style="display:inline;">
                        <input type="hidden" name="item_id" value="99">
                        <input type="number" name="quantity" value="1" min="1">
                        <button type="submit">Purchase</button>
                    </form>
                    <p style="color:#666;font-size:0.9em;">⚠️ 残高不足のため購入不可</p>
                </div>
            </div>
        </body>
        </html>
    ''', credit=session['credit'])

@app.route('/buy', methods=['POST'])
def buy():
    item_id = int(request.form['item_id'])
    quantity = int(request.form['quantity'])
    
    if item_id not in ITEMS:
        return '<p>商品が見つかりません</p><a href="/">戻る</a>'
    
    item = ITEMS[item_id]
    
    # ❌ 脆弱性: マイナス数量のチェックがない
    total_price = item['price'] * quantity
    
    # ❌ 残高チェックが不十分
    if session['credit'] >= total_price:
        session['credit'] -= total_price
        
        # Flag Itemの場合、フラグを表示
        if item_id == 99:
            flag = os.environ.get('FLAG', 'SolCTF{logic_error_negative_quantity}')
            return render_template_string('''
                <div style="background:#0a0a0a;color:#ffaa00;font-family:monospace;padding:20px;">
                    <h1>Purchase Complete!</h1>
                    <p>{{ item_name }} を購入しました</p>
                    <hr>
                    <div style="border:2px solid #ff0080;padding:15px;background:#1a0a0a;">
                        <h2>[CLASSIFIED DATA]</h2>
                        <p>Flag: <code style="color:#0f0;">{{ flag }}</code></p>
                    </div>
                    <p>残高: {{ credit }} 円</p>
                    <a href="/">戻る</a>
                </div>
            ''', item_name=item['name'], flag=flag, credit=session['credit'])
        else:
            return f'<p>{item["name"]} を購入しました</p><p>残高: {session["credit"]} 円</p><a href="/">戻る</a>'
    else:
        return '<p>残高不足です</p><a href="/">戻る</a>'

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
```

---

## 攻略手順

### ステップ1: 初期状態の確認

1. `http://{{CONTAINER_HOST}}/` にアクセス
2. 初期クレジット: 1000円
3. Flag Item: 1,000,000円（購入不可）

### ステップ2: 通常の購入を試す

Common Part（100円）を購入 → 成功  
残高: 900円

### ステップ3: ロジックエラーを発見

**仮説**: マイナス数量が許可されているかも？

### ステップ4: マイナス数量で購入

**方法**: ブラウザの開発者ツールでHTMLを編集

1. F12キーで開発者ツールを開く
2. Elementsタブで `<input type="number" name="quantity" value="1" min="1">` を見つける
3. `min="1"` を削除、または `value="-10"` に変更
4. 数量: `-10` を入力
5. Common Part（100円）を購入

**計算**:
```
total_price = 100 * (-10) = -1000円
credit = 1000 - (-1000) = 2000円
```

**残高が増える！**

### ステップ5: クレジットを増やす

マイナス数量で購入を繰り返し、残高を1,000,000円以上にする:

```
-10個 × 100円 = -1000円消費 → +1000円獲得
繰り返す → 1,000,000円以上にする
```

または、一気に:
```
数量: -10000
Common Part購入
→ 1,000,000円獲得
```

### ステップ6: Flag Item購入

1. 残高が1,000,000円以上になったら
2. Flag Item（#99）を購入
3. フラグが表示される: `SolCTF{logic_error_negative_quantity}`

---

## 🎓 初心者向け: Logic Errorの理解

### ビジネスロジックとは

アプリケーションの「業務ルール」のこと:
- 商品価格の計算
- 在庫管理
- ユーザー権限の検証

### この問題のロジックエラー

```python
# 期待される動作
quantity = 1
total = 100 * 1 = 100円消費

# 実際の動作（マイナス数量）
quantity = -1
total = 100 * (-1) = -100円消費
credit = 1000 - (-100) = 1100円（増える！）
```

**問題**: 「数量は正の整数」という前提条件を検証していない

---

## 難易度

```json
{
  "difficulty": 3,
  "difficulty_factors": {
    "tech": 2,
    "read": 3,
    "explore": 4
  }
}
```

---

## Story Hook

```
Afterlife Marketplaceの地下マーケットシステムが、内部監査の対象となった。このショップは違法アイテムを販売しており、ユーザーには初期クレジット1000円が付与される。しかし、高額な「FLAG ITEM」（100万円）は通常の方法では購入不可能だ。あなたの任務は、ビジネスロジックの欠陥を発見し、クレジットを不正に増やして高額アイテムを購入し、そこに含まれる機密フラグを入手することだ。
```

## タグ

- Web
- Logic Error
- Integer Overflow
- Business Logic
- Intermediate
- E-commerce

## 対策

```python
# ✅ セキュアな実装

# 1. 数量の検証
quantity = int(request.form['quantity'])
if quantity <= 0:
    return "Error: Invalid quantity"

if quantity > 100:
    return "Error: Quantity too large"

# 2. オーバーフローのチェック
MAX_INT = 2**31 - 1
if total_price > MAX_INT or total_price < 0:
    return "Error: Invalid price calculation"

# 3. サーバー側で価格を管理
# フロントエンドからの価格は信頼しない
server_price = ITEMS[item_id]['price']
total = server_price * quantity  # サーバー側で計算
```

