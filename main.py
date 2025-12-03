"""
CTF Challenge Generator - Streamlit Web Application

PDFファイルやテキストファイルからCTF問題を生成するWebアプリケーション
"""

import streamlit as st
import os
from pathlib import Path
from typing import Optional
import PyPDF2
import io

from src.generate import CTFChallengeGenerator
from src.models import CTFOutput, CTFChallenge

# ページ設定
st.set_page_config(
    page_title="CTF Challenge Generator",
    page_icon="🏴",
    layout="wide"
)

# タイトル
st.title("🏴 CTF Challenge Generator")
st.markdown("---")
st.markdown("### 脆弱性の解説からCTF問題を自動生成")

# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
    
    # APIキーの確認
    api_key = st.text_input(
        "Gemini API Key",
        value=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "",
        type="password",
        help=".envファイルに設定されている場合は自動で読み込まれます"
    )
    
    if not api_key:
        st.warning("⚠️ APIキーを入力してください")
    
    st.markdown("---")
    
    # 問題数の設定
    num_challenges = st.slider(
        "生成する問題数",
        min_value=1,
        max_value=5,
        value=1,
        help="生成するCTF問題の数を選択してください"
    )
    
    st.markdown("---")
    st.markdown("### 📖 使い方")
    st.markdown("""
    1. PDFファイルまたはテキストをアップロード
    2. 「CTF問題を生成」ボタンをクリック
    3. 生成された脆弱なコードとWriteupを確認
    """)


def extract_text_from_pdf(pdf_file) -> str:
    """
    PDFファイルからテキストを抽出
    
    Args:
        pdf_file: アップロードされたPDFファイル
    
    Returns:
        抽出されたテキスト
    """
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"PDFの読み込みに失敗しました: {e}")
        return ""


def display_challenge(ctf_output: CTFOutput):
    """
    生成されたCTF問題を表示
    
    Args:
        ctf_output: 生成されたCTF問題
    """
    # 各問題を表示
    for i, challenge in enumerate(ctf_output.challenges, 1):
        with st.container():
            st.header(f"🏴 {challenge.title}")
            
            # メタ情報
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**難易度:** {challenge.difficulty}/5")
            with col2:
                st.markdown(f"**フラグ:** `{challenge.flag}`")
            
            st.markdown("---")
            
            # 問題文
            st.subheader("📋 問題文")
            st.markdown(challenge.description)
            st.markdown("")
            
            # 脆弱なコード
            st.subheader("💻 脆弱なコード")
            st.code(challenge.vulnerable_code, language="python")
            st.markdown("")
            
            # Writeup（折りたたみ可能）
            with st.expander("📖 攻略解説 (Writeup)", expanded=False):
                st.markdown(challenge.writeup)
            
            st.markdown("---")
    
    # JSONダウンロードボタン
    import json
    ctf_json = json.dumps(ctf_output.model_dump(), ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 CTF問題をJSON形式でダウンロード",
        data=ctf_json,
        file_name="ctf_challenge.json",
        mime="application/json"
    )


# メインコンテンツ
st.markdown("### 📄 ファイルアップロード")

# ファイルアップローダー
uploaded_file = st.file_uploader(
    "PDFファイルまたはテキストファイルをアップロードしてください",
    type=["pdf", "txt"],
    help="PDFファイルまたはテキストファイルを選択してください"
)

# テキスト入力（ファイルアップロードの代替）
st.markdown("---")
st.markdown("### または、テキストを直接入力")
text_input = st.text_area(
    "テキストを入力してください",
    height=200,
    help="PDFファイルの代わりに、テキストを直接入力することもできます"
)

# CTF問題生成ボタン
st.markdown("---")

if st.button("🚀 CTF問題を生成", type="primary", use_container_width=True):
    if not api_key:
        st.error("❌ APIキーを入力してください")
        st.stop()
    
    # テキストの取得
    context = ""
    
    if uploaded_file is not None:
        # ファイルからテキストを抽出
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        if file_extension == ".pdf":
            with st.spinner("PDFファイルを読み込んでいます..."):
                context = extract_text_from_pdf(uploaded_file)
        elif file_extension == ".txt":
            context = uploaded_file.read().decode("utf-8")
        else:
            st.error("サポートされていないファイル形式です")
            st.stop()
    elif text_input:
        context = text_input
    else:
        st.warning("⚠️ ファイルをアップロードするか、テキストを入力してください")
        st.stop()
    
    if not context or not context.strip():
        st.error("❌ テキストが空です。有効なテキストを入力してください")
        st.stop()
    
    # CTF問題生成
    try:
        with st.spinner("🤖 CTF問題を生成中... 数秒かかる場合があります"):
            generator = CTFChallengeGenerator(api_key=api_key)
            ctf_output = generator.generate_challenge(
                context=context,
                num_challenges=num_challenges
            )
        
        st.success("✅ CTF問題の生成が完了しました！")
        st.markdown("---")
        
        # CTF問題を表示
        display_challenge(ctf_output)
        
    except ValueError as e:
        st.error(f"❌ エラー: {e}")
    except Exception as e:
        st.error(f"❌ CTF問題生成に失敗しました: {e}")
        st.exception(e)

# フッター
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "CTF Challenge Generator - Powered by Gemini 2.0 Flash"
    "</div>",
    unsafe_allow_html=True
)

