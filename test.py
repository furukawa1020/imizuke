#!/usr/bin/env python3
"""
ことイミ日記 - テストスクリプト
基本機能の動作確認を行います
"""

import json
import requests
import time
import sqlite3
from server import DatabaseManager

def test_database():
    """データベース機能のテスト"""
    print("=== データベーステスト ===")
    
    try:
        db = DatabaseManager('test_kotoiminiki.db')
        print("✅ データベース初期化成功")
        
        # テストデータの挿入
        test_data = {
            'user_id_hash': 'test_user_123',
            'timestamp': '2025-09-21T10:30:00Z',
            'consent': True,
            'mode': 'social',
            'event_tag': 'work',
            'event_text': 'テスト用の出来事',
            'meaning_text': 'これはテスト用の意味づけです。十分な長さがあります。',
            'meaning_tag': 'learning,test',
            'rt_ms': 2500,
            'quality_flags': '{}'
        }
        
        record_id = db.insert_record(test_data)
        print(f"✅ レコード挿入成功: {record_id}")
        
        # 分布データの取得テスト
        distribution = db.get_distribution_data('work')
        print(f"✅ 分布データ取得成功: {distribution}")
        
        # 重複チェックテスト
        is_duplicate = db.check_duplicate('test_user_123', 'work', 'これはテスト用の意味づけです。十分な長さがあります。')
        print(f"✅ 重複チェック成功: {is_duplicate}")
        
        return True
        
    except Exception as e:
        print(f"❌ データベーステストエラー: {e}")
        return False
    
    finally:
        # テストデータベースを削除
        import os
        if os.path.exists('test_kotoiminiki.db'):
            os.remove('test_kotoiminiki.db')

def test_server_api():
    """サーバーAPI機能のテスト"""
    print("\n=== サーバーAPIテスト ===")
    
    base_url = 'http://localhost:8000'
    
    try:
        # ヘルスチェック
        response = requests.get(f'{base_url}/health', timeout=5)
        if response.status_code == 200:
            print("✅ サーバー接続成功")
        else:
            print(f"❌ サーバー接続失敗: {response.status_code}")
            return False
        
        # データ送信テスト
        test_data = {
            'id': 'test_entry_001',
            'user_id_hash': 'test_user_api',
            'timestamp': '2025-09-21T10:30:00Z',
            'consent': True,
            'mode': 'social',
            'event_tag': 'test',
            'event_text': 'APIテスト用の出来事',
            'meaning_text': 'これはAPIテスト用の意味づけです。十分な長さを持っています。',
            'meaning_tag': 'test,api',
            'rt_ms': 1500,
            'quality_flags': '{}'
        }
        
        response = requests.post(f'{base_url}/submit', 
                               json=test_data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            print("✅ データ送信成功")
            result = response.json()
            print(f"   レスポンス: {result}")
        else:
            print(f"❌ データ送信失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            return False
        
        # 分布データ取得テスト
        response = requests.get(f'{base_url}/fetch?event_tag=test', timeout=5)
        
        if response.status_code == 200:
            print("✅ 分布データ取得成功")
            distribution_data = response.json()
            print(f"   分布: {distribution_data}")
        else:
            print(f"❌ 分布データ取得失敗: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません")
        print("   python server.py でサーバーを起動してからテストしてください")
        return False
    except Exception as e:
        print(f"❌ APIテストエラー: {e}")
        return False

def test_quality_flags():
    """品質フラグ機能のテスト"""
    print("\n=== 品質フラグテスト ===")
    
    try:
        db = DatabaseManager('test_quality.db')
        
        # 短すぎるテキストのテスト
        short_data = {
            'user_id_hash': 'test_quality_1',
            'timestamp': '2025-09-21T10:30:00Z',
            'consent': True,
            'mode': 'solo',
            'event_tag': 'test',
            'event_text': '',
            'meaning_text': '短い',  # 短すぎる
            'meaning_tag': '',
            'rt_ms': 5000,
            'quality_flags': '{"too_short": true}'
        }
        
        record_id = db.insert_record(short_data)
        print(f"✅ 短文データ挿入成功: {record_id}")
        
        # スパムフラグのテスト
        spam_data = {
            'user_id_hash': 'test_quality_2',
            'timestamp': '2025-09-21T10:30:01Z',
            'consent': True,
            'mode': 'social',
            'event_tag': 'test',
            'event_text': '',
            'meaning_text': 'これは十分な長さの意味づけテキストです。',
            'meaning_tag': '',
            'rt_ms': 100,  # 短すぎる反応時間
            'quality_flags': '{"spam": true}'
        }
        
        record_id = db.insert_record(spam_data)
        print(f"✅ スパムフラグデータ挿入成功: {record_id}")
        
        # 品質フィルタリングされた分布の取得
        distribution = db.get_distribution_data('test')
        print(f"✅ フィルタリング済み分布取得: {distribution}")
        
        return True
        
    except Exception as e:
        print(f"❌ 品質フラグテストエラー: {e}")
        return False
    
    finally:
        import os
        if os.path.exists('test_quality.db'):
            os.remove('test_quality.db')

def run_all_tests():
    """全てのテストを実行"""
    print("ことイミ日記 - 自動テスト開始")
    print("=" * 50)
    
    results = []
    
    # データベーステスト
    results.append(("データベース", test_database()))
    
    # 品質フラグテスト
    results.append(("品質フラグ", test_quality_flags()))
    
    # サーバーAPIテスト（サーバーが起動している場合のみ）
    print("\nサーバーAPIテストを実行しますか？")
    print("（事前に 'python server.py' でサーバーを起動してください）")
    user_input = input("y/n: ").lower().strip()
    
    if user_input == 'y':
        results.append(("サーバーAPI", test_server_api()))
    
    # 結果まとめ
    print("\n" + "=" * 50)
    print("テスト結果まとめ")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name:<15}: {status}")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print(f"\n成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 全てのテストが成功しました！")
        return True
    else:
        print("⚠️  いくつかのテストが失敗しました。")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    
    if success:
        print("\n✅ ことイミ日記の実装が完了しました！")
        print("\n起動方法:")
        print("1. python server.py")
        print("2. ブラウザで http://localhost:8000 にアクセス")
        print("\nまたは:")
        print("start.bat をダブルクリック（Windows）")
    else:
        print("\n❌ 問題が発生しています。ログを確認してください。")