#!/usr/bin/env python3
"""
実際のセキュリティテスト - サーバーに対する攻撃シミュレーション
"""

import requests
import time
import json

def test_xss_injection():
    """XSS攻撃テスト"""
    print("=== XSS攻撃テスト ===")
    
    malicious_payloads = [
        '<script>alert("XSS")</script>',
        'javascript:alert(1)',
        '<img src="x" onerror="alert(1)">',
        '<iframe src="javascript:alert(1)"></iframe>'
    ]
    
    for payload in malicious_payloads:
        test_data = {
            'id': 'security_test_001',
            'user_id_hash': 'anon_test_123',
            'timestamp': '2025-09-21T10:30:00Z',
            'consent': True,
            'mode': 'social',
            'event_tag': 'work_late',
            'event_text': payload,  # 悪意のあるペイロード
            'meaning_text': 'セキュリティテスト用の意味づけです。',
            'meaning_tag': 'test',
            'rt_ms': 1000,
            'quality_flags': '{}'
        }
        
        try:
            response = requests.post('http://localhost:8001/submit', 
                                   json=test_data, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=5)
            
            print(f"ペイロード: {payload[:50]}...")
            print(f"ステータス: {response.status_code}")
            
            if response.status_code == 200:
                print("⚠️ 受け入れられました - サニタイゼーションを確認")
            elif response.status_code == 400:
                print("✅ 拒否されました - バリデーション機能が動作")
            else:
                print(f"❓ 予期しないレスポンス: {response.status_code}")
            
            print("---")
            time.sleep(0.5)  # レート制限回避
            
        except Exception as e:
            print(f"❌ エラー: {e}")

def test_rate_limiting():
    """レート制限テスト"""
    print("\n=== レート制限テスト ===")
    
    test_data = {
        'id': 'rate_test_001',
        'user_id_hash': 'anon_rate_test',
        'timestamp': '2025-09-21T10:30:00Z',
        'consent': True,
        'mode': 'solo',
        'event_tag': 'work_late',
        'event_text': 'レート制限テスト',
        'meaning_text': 'これはレート制限のテストです。',
        'meaning_tag': 'test',
        'rt_ms': 1000,
        'quality_flags': '{}'
    }
    
    success_count = 0
    rate_limited_count = 0
    
    print("35回のリクエストを高速送信...")
    for i in range(35):
        test_data['id'] = f'rate_test_{i:03d}'
        
        try:
            response = requests.post('http://localhost:8001/submit', 
                                   json=test_data,
                                   timeout=2)
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"🚫 リクエスト{i+1}: レート制限発動 (429)")
            
        except Exception as e:
            print(f"❌ リクエスト{i+1} エラー: {e}")
    
    print(f"\n結果:")
    print(f"成功: {success_count}")
    print(f"レート制限: {rate_limited_count}")
    
    if rate_limited_count > 0:
        print("✅ レート制限が正常に動作しています")
    else:
        print("⚠️ レート制限が動作していない可能性があります")

def test_sql_injection():
    """SQLインジェクション攻撃テスト"""
    print("\n=== SQLインジェクション攻撃テスト ===")
    
    sql_payloads = [
        "'; DROP TABLE records; --",
        "' OR '1'='1",
        "'; SELECT * FROM records; --",
        "admin'--",
        "' UNION SELECT * FROM records --"
    ]
    
    for payload in sql_payloads:
        test_data = {
            'id': 'sql_test_001',
            'user_id_hash': payload,  # SQLインジェクション試行
            'timestamp': '2025-09-21T10:30:00Z',
            'consent': True,
            'mode': 'social',
            'event_tag': 'work_late',
            'event_text': 'SQLインジェクションテスト',
            'meaning_text': payload,  # ここでも試行
            'meaning_tag': 'test',
            'rt_ms': 1000,
            'quality_flags': '{}'
        }
        
        try:
            response = requests.post('http://localhost:8001/submit', 
                                   json=test_data,
                                   timeout=5)
            
            print(f"ペイロード: {payload[:30]}...")
            print(f"ステータス: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ バリデーションエラー - 適切に拒否")
            elif response.status_code == 200:
                print("⚠️ 受け入れられました - パラメータ化クエリで安全化済み")
            
            print("---")
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ エラー: {e}")

def test_invalid_data():
    """不正データテスト"""
    print("\n=== 不正データテスト ===")
    
    invalid_tests = [
        {
            'name': '不正なevent_tag',
            'data': {
                'event_tag': 'invalid_tag_not_allowed',
                'meaning_text': '正常な意味づけです。'
            }
        },
        {
            'name': '不正なmode',
            'data': {
                'mode': 'invalid_mode',
                'meaning_text': '正常な意味づけです。'
            }
        },
        {
            'name': '短すぎる意味づけ',
            'data': {
                'meaning_text': 'x'  # 5文字未満
            }
        },
        {
            'name': '不正なuser_id_hash形式',
            'data': {
                'user_id_hash': 'invalid_format_hash',
                'meaning_text': '正常な意味づけです。'
            }
        }
    ]
    
    base_data = {
        'id': 'invalid_test_001',
        'user_id_hash': 'anon_test_valid',
        'timestamp': '2025-09-21T10:30:00Z',
        'consent': True,
        'mode': 'solo',
        'event_tag': 'work_late',
        'event_text': 'テストデータ',
        'meaning_text': '正常な意味づけテストです。',
        'meaning_tag': 'test',
        'rt_ms': 1000,
        'quality_flags': '{}'
    }
    
    for test_case in invalid_tests:
        test_data = base_data.copy()
        test_data.update(test_case['data'])
        
        try:
            response = requests.post('http://localhost:8001/submit', 
                                   json=test_data,
                                   timeout=5)
            
            print(f"テスト: {test_case['name']}")
            print(f"ステータス: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ 適切に拒否されました")
            else:
                print("⚠️ 予期しないレスポンス")
            
            print("---")
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ エラー: {e}")

def main():
    """メインのセキュリティテスト実行"""
    print("🔒 ことイミ日記 - セキュリティテスト開始")
    print("=" * 60)
    
    try:
        # サーバーの生存確認
        response = requests.get('http://localhost:8001/health', timeout=5)
        if response.status_code != 200:
            print("❌ サーバーに接続できません")
            return
        
        print("✅ サーバー接続確認")
        print("=" * 60)
        
        # 各セキュリティテストを実行
        test_invalid_data()
        test_xss_injection()
        test_sql_injection()
        test_rate_limiting()
        
        print("\n" + "=" * 60)
        print("🏁 セキュリティテスト完了")
        print("\n⚠️ 注意: このテストは開発環境でのみ実行してください")
        
    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません")
        print("python server.py 8001 でサーバーを起動してください")

if __name__ == '__main__':
    main()