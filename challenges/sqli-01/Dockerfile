FROM python:3.11-slim

# セキュリティ: 一般ユーザーで実行
RUN useradd -m -u 1000 ctfuser && \
    mkdir -p /app && \
    chown -R ctfuser:ctfuser /app

WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY main.py .

# ユーザーを切り替え
USER ctfuser

# ポートを公開
EXPOSE 8000

# 環境変数（Flag注入）
ENV CTF_FLAG=SolCTF{y0u_f0und_7h3_sql_m4s73r_k3y}

# アプリケーションを起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

