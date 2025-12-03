"""
QuizGenerator 単体テスト

短いテキストを入力して、クイズが生成されるか確認するテストスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.generate import QuizGenerator
from src.models import QuizOutput


def test_quiz_generation():
    """
    QuizGeneratorの基本的な動作をテスト
    
    短いテキストを入力して、クイズが正しく生成されるか確認します。
    """
    print("=" * 70)
    print("QuizGenerator 単体テスト")
    print("=" * 70)
    print()
    
    # テスト用の短いテキスト
    test_context = """
    SQLインジェクション（SQL Injection）は、Webアプリケーションの脆弱性の一つです。
    攻撃者が悪意のあるSQLコードを入力フィールドに注入することで、
    データベースに対して意図しない操作を実行させることができます。
    
    対策としては、プリペアドステートメント（Prepared Statement）の使用が推奨されます。
    これにより、ユーザー入力をSQLコマンドとして解釈されないようにすることができます。
    """
    
    print("【テストコンテキスト】")
    print(test_context.strip())
    print()
    print("-" * 70)
    print()
    
    try:
        # QuizGeneratorを初期化
        print("1. QuizGeneratorを初期化中...")
        generator = QuizGenerator()
        print("   ✓ 初期化成功")
        print()
        
        # クイズを生成
        print("2. クイズを生成中...")
        print("   （Gemini APIを呼び出しています。数秒かかる場合があります）")
        print()
        
        output: QuizOutput = generator.generate_quiz(
            context=test_context,
            num_questions=2  # テスト用に2問のみ生成
        )
        
        print("   ✓ クイズ生成成功")
        print()
        print("-" * 70)
        print()
        
        # 結果を表示
        print("【生成されたクイズ】")
        print()
        
        quiz_set = output.quiz_set
        if quiz_set.title:
            print(f"タイトル: {quiz_set.title}")
            print()
        print(f"問題数: {len(quiz_set.questions)}")
        print()
        
        for i, question in enumerate(quiz_set.questions, 1):
            print(f"問題 {i}:")
            print(f"  難易度: {question.difficulty}/5")
            print(f"  タグ: {', '.join(question.tags) if question.tags else 'なし'}")
            print(f"  問題文: {question.question_text}")
            print()
            print("  選択肢:")
            for j, option in enumerate(question.options, 1):
                correct_mark = "✓" if option.is_correct else " "
                print(f"    {correct_mark} {j}. {option.text}")
                if option.explanation:
                    print(f"       説明: {option.explanation}")
            print()
            print("-" * 70)
            print()
        
        # 検証
        print("【検証結果】")
        all_valid = True
        
        # 問題数チェック
        if len(quiz_set.questions) == 0:
            print("  ✗ 問題が生成されていません")
            all_valid = False
        else:
            print(f"  ✓ 問題数: {len(quiz_set.questions)}")
        
        # 各問題の検証
        for i, question in enumerate(quiz_set.questions, 1):
            # 選択肢数チェック
            if len(question.options) < 2:
                print(f"  ✗ 問題{i}: 選択肢が少なすぎます（{len(question.options)}個）")
                all_valid = False
            else:
                print(f"  ✓ 問題{i}: 選択肢数 {len(question.options)}")
            
            # 正解の数チェック
            correct_count = sum(1 for opt in question.options if opt.is_correct)
            if correct_count != 1:
                print(f"  ✗ 問題{i}: 正解が{correct_count}個です（1個である必要があります）")
                all_valid = False
            else:
                print(f"  ✓ 問題{i}: 正解が1個")
        
        print()
        if all_valid:
            print("=" * 70)
            print("✓ すべてのテストが成功しました！")
            print("=" * 70)
            return True
        else:
            print("=" * 70)
            print("✗ 一部のテストが失敗しました")
            print("=" * 70)
            return False
            
    except ValueError as e:
        print()
        print("=" * 70)
        print("✗ エラー: 設定エラー")
        print("=" * 70)
        print(f"エラーメッセージ: {e}")
        print()
        print("【対処方法】")
        print("1. .envファイルにGEMINI_API_KEYを設定してください")
        print("2. API_KEYS_SETUP.mdを参照してAPIキーを取得してください")
        return False
        
    except Exception as e:
        print()
        print("=" * 70)
        print("✗ エラー: クイズ生成に失敗しました")
        print("=" * 70)
        print(f"エラーメッセージ: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_quiz_generation()
    sys.exit(0 if success else 1)

