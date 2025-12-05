# Encrypted Communication: Weak RSA Attack

## シナリオ

あなたは、Kang Tao Corporation の暗号解析チームとして、傍受された暗号化通信の解読を命じられた。

**ターゲット**: RSA暗号化された機密通信  
**目的**: 脆弱なRSA鍵を解析し、暗号文を復号せよ  
**インテル**: 傍受された通信はRSA暗号で保護されているが、使用されている公開鍵の指数`e`が異常に小さい（`e=3`）、または素数`N`が小さすぎて素因数分解可能である可能性がある。あなたの任務は、公開鍵から秘密鍵を復元し、暗号文を復号して機密フラグを入手することだ。

**ミッション**: RSA暗号を解読し、フラグを取得せよ。

---

## 技術的背景: RSA暗号とは

### RSA暗号の基本

**公開鍵暗号**の一種で、以下の要素から構成されます:

- **公開鍵**: `(N, e)` - 誰でも知ることができる
- **秘密鍵**: `(N, d)` - 暗号化した人だけが知っている
- **N**: 2つの大きな素数 `p` と `q` の積 (`N = p * q`)
- **e**: 公開鍵指数（通常は65537）
- **d**: 秘密鍵指数

**暗号化**: `C = M^e mod N`  
**復号**: `M = C^d mod N`

### 脆弱性: 小さいeまたは小さいN

1. **e=3 が小さすぎる場合**:
   - メッセージが小さいと、`M^3 < N` となり、modなしで復号可能
   - 3乗根を取るだけで平文が得られる

2. **Nが小さすぎる場合**:
   - 素因数分解が可能
   - `N = p * q` から `p` と `q` を求められる
   - 秘密鍵 `d` を計算できる

---

## 脆弱なコードの仕様

### 問題形式

**この問題はWebアプリではなく、暗号解読問題です。**

### 提供ファイル

#### 1. `chall.py` (暗号化スクリプト)

```python
from Crypto.Util.number import getPrime, bytes_to_long, long_to_bytes
import os

# フラグ
flag = b"SolCTF{weak_rsa_small_e_attack}"

# RSA鍵生成
# ❌ 脆弱性: e=3 が小さすぎる
e = 3
p = getPrime(512)  # 512ビット素数（小さめ）
q = getPrime(512)
N = p * q

# 暗号化
m = bytes_to_long(flag)
c = pow(m, e, N)

# 公開情報を出力
print(f"公開鍵:")
print(f"N = {N}")
print(f"e = {e}")
print(f"")
print(f"暗号文:")
print(f"c = {c}")

# output.txt に保存
with open('output.txt', 'w') as f:
    f.write(f"N = {N}\n")
    f.write(f"e = {e}\n")
    f.write(f"c = {c}\n")

print("\n公開情報を output.txt に保存しました")
```

#### 2. `output.txt` (公開情報)

```
N = 9876543210987654321098765432109876543210987654321098765432109876543210
e = 3
c = 1234567890123456789012345678901234567890123456789012345678901234567890
```

---

## 攻略手順

### ステップ1: 公開情報の確認

提供ファイル:
- `chall.py`: 暗号化スクリプト（参考用）
- `output.txt`: 公開鍵（N, e）と暗号文（c）

### ステップ2: 脆弱性の特定

**`e = 3` が異常に小さい** ← これが脆弱性

通常、RSAでは `e = 65537` を使用する。

### ステップ3: 復号スクリプトの作成

**解法**: eが小さい場合の攻撃（Low Public Exponent Attack）

```python
import gmpy2
from Crypto.Util.number import long_to_bytes

# output.txt から値を読み込む
N = 9876543210987654321098765432109876543210987654321098765432109876543210
e = 3
c = 1234567890123456789012345678901234567890123456789012345678901234567890

# e=3の場合、m^3 < N の可能性がある
# その場合、modなしで復号可能（3乗根を取る）

# k=0から試す（c + k*N の3乗根を取る）
k = 0
while True:
    # c + k*N の3乗根を取る
    m_candidate, is_exact = gmpy2.iroot(c + k * N, e)
    
    if is_exact:
        # 3乗根が整数 → これが平文
        m = int(m_candidate)
        flag = long_to_bytes(m)
        
        if b'SolCTF' in flag:
            print(f"Flag found: {flag.decode()}")
            break
    
    k += 1
    
    if k > 100:
        print("解読失敗")
        break
```

### ステップ4: フラグ取得

**実行**:
```bash
python3 solve.py
```

**結果**:
```
Flag found: SolCTF{weak_rsa_small_e_attack}
```

---

## 🎓 初心者向け: RSA暗号の基礎

### なぜe=3が危険なのか

**通常のRSA（e=65537）**:
```
M^65537 mod N = C
→ Mは巨大な数になり、mod Nで小さくなる
→ 3乗根では復号不可能
```

**e=3の場合**:
```
M^3 mod N = C

もし M^3 < N なら:
M^3 = C (modなし)
→ 3乗根を取るだけ: M = ∛C
```

### 実例

```python
# 例: フラグが短い場合
flag = "SolCTF{test}"
M = bytes_to_long(flag.encode())  # 例: 123456789...
M^3 = 非常に大きい数

# しかし、Nがさらに大きければ:
M^3 < N
→ M^3 mod N = M^3
→ ∛(M^3) = M
```

---

## 難易度

```json
{
  "difficulty": 3,
  "difficulty_factors": {
    "tech": 4,
    "read": 2,
    "explore": 2
  }
}
```

---

## Story Hook

```
Kang Tao Corporationの暗号解析チームが、傍受された暗号化通信の解読を試みている。この通信はRSA暗号で保護されているが、使用されている公開鍵指数が異常に小さい（e=3）ことが判明した。あなたの任務は、この脆弱性を突いて秘密鍵を復元し、暗号文を復号して機密フラグを入手することだ。
```

## タグ

- Crypto
- RSA
- Weak Encryption
- Intermediate
- Mathematics

## 実装上の注意

### Flask Webアプリとして実装する場合

```python
@app.route('/')
def index():
    # output.txt の内容を表示
    with open('output.txt', 'r') as f:
        content = f.read()
    
    return render_template_string('''
        <h1>KANG TAO CORP</h1>
        <h2>Encrypted Communication Analysis</h2>
        <hr>
        <p>傍受された暗号化通信:</p>
        <pre style="background:#000;color:#0f0;padding:10px;">{{ content }}</pre>
        <p>ダウンロード: <a href="/download/output.txt">output.txt</a></p>
        <p>参考: <a href="/download/chall.py">chall.py</a></p>
    ''', content=content)

@app.route('/download/<filename>')
def download(filename):
    if filename == 'output.txt':
        with open('output.txt', 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/plain'}
    elif filename == 'chall.py':
        with open('chall.py', 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/plain'}
```

---

## 対策

```python
# ✅ セキュアな実装

# 1. eを十分大きくする
e = 65537  # 推奨値

# 2. Nを十分大きくする
p = getPrime(2048)  # 2048ビット以上
q = getPrime(2048)

# 3. パディングを使用
from Crypto.Cipher import PKCS1_OAEP
cipher = PKCS1_OAEP.new(key)
```

