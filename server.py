#!/usr/bin/env python3
"""
ことイミ日記 - Meaning Diversity Logger Server
軽量・依存最小のWebサーバー実装
"""

import json
import sqlite3
import hashlib
import datetime
import urllib.parse
import html
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
import threading
import time

class MeaningDiversityAnalyzer:
    """意味づけデータの分析クラス"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_connection(self):
        """データベース接続を取得"""
        return sqlite3.connect(self.db_path)
    
    def analyze_event_diversity(self, event_tag=None):
        """イベントの意味づけ多様性を分析"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 基本統計
            cursor.execute("SELECT COUNT(*) FROM meanings")
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                return {"status": "no_data", "message": "データが存在しません"}
            
            # カテゴリ分布
            cursor.execute("SELECT event_category, COUNT(*) FROM meanings GROUP BY event_category")
            categories = dict(cursor.fetchall())
            
            # 意味づけタグ分布
            cursor.execute("SELECT meaning_tags FROM meanings WHERE meaning_tags IS NOT NULL")
            tag_counts = {}
            for row in cursor.fetchall():
                tags = row[0].split(',') if row[0] else []
                for tag in tags:
                    tag = tag.strip()
                    if tag:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            return {
                "status": "success",
                "total_count": total_count,
                "categories": categories,
                "tag_distribution": tag_counts,
                "entropy_text": 0.0,  # 簡易実装
                "entropy_tags": 0.0   # 簡易実装
            }
        finally:
            conn.close()

    def compare_solo_vs_social(self, event_tag=None):
        """Solo vs Social モードの比較分析"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT mode, COUNT(*) FROM meanings GROUP BY mode")
            mode_counts = dict(cursor.fetchall())
            
            return {
                "status": "success",
                "mode_distribution": mode_counts,
                "solo_count": mode_counts.get("solo", 0),
                "social_count": mode_counts.get("social", 0)
            }
        finally:
            conn.close()
    
    def analyze_revision_impact(self, event_tag=None):
        """修正の影響分析"""
        return {
            "status": "success",
            "revision_count": 0,
            "impact_score": 0.0
        }
    
    def generate_comprehensive_report(self):
        """包括的なレポート生成"""
        diversity = self.analyze_event_diversity()
        comparison = self.compare_solo_vs_social()
        
        return {
            "status": "success",
            "diversity_analysis": diversity,
            "mode_comparison": comparison,
            "generated_at": datetime.datetime.now().isoformat()
        }


class MeaningDiversityServer(BaseHTTPRequestHandler):
    
    # レート制限用のクラス変数
    _request_counts = {}
    _blocked_ips = {}
    _last_cleanup = time.time()
    
    # 設定値
    RATE_LIMIT_REQUESTS = 30  # 1分間あたりの最大リクエスト数
    RATE_LIMIT_WINDOW = 60    # 時間窓(秒)
    RATE_LIMIT_BLOCK_TIME = 300  # ブロック時間(秒)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def check_rate_limit(self):
        """レート制限のチェック"""
        client_ip = self.client_address[0]
        current_time = time.time()
        
        # 定期的にカウンターをクリーンアップ
        if current_time - self._last_cleanup > self.RATE_LIMIT_WINDOW:
            self._cleanup_rate_limit_data()
            self._last_cleanup = current_time
        
        # ブロックされたIPかチェック
        if client_ip in self._blocked_ips:
            if current_time - self._blocked_ips[client_ip] < self.RATE_LIMIT_BLOCK_TIME:
                return False
            else:
                # ブロック期間が過ぎたので解除
                del self._blocked_ips[client_ip]
        
        # リクエスト数をカウント
        if client_ip not in self._request_counts:
            self._request_counts[client_ip] = []
        
        # 古いリクエストを削除
        cutoff_time = current_time - self.RATE_LIMIT_WINDOW
        self._request_counts[client_ip] = [
            req_time for req_time in self._request_counts[client_ip] 
            if req_time > cutoff_time
        ]
        
        # リクエスト制限チェック
        if len(self._request_counts[client_ip]) >= self.RATE_LIMIT_REQUESTS:
            # IPをブロック
            self._blocked_ips[client_ip] = current_time
            return False
        
        # リクエストを記録
        self._request_counts[client_ip].append(current_time)
        return True
    
    def _cleanup_rate_limit_data(self):
        """古いレート制限データをクリーンアップ"""
        current_time = time.time()
        cutoff_time = current_time - self.RATE_LIMIT_WINDOW
        
        # 古いリクエストカウントを削除
        for ip in list(self._request_counts.keys()):
            self._request_counts[ip] = [
                req_time for req_time in self._request_counts[ip] 
                if req_time > cutoff_time
            ]
            if not self._request_counts[ip]:
                del self._request_counts[ip]
        
        # 期限切れのブロックを削除
        for ip in list(self._blocked_ips.keys()):
            if current_time - self._blocked_ips[ip] >= self.RATE_LIMIT_BLOCK_TIME:
                del self._blocked_ips[ip]
    
    def do_GET(self):
        """GET リクエストの処理"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # CORS ヘッダーを設定
        self.send_cors_headers()
        
        if path == '/':
            # index.html を返す
            self.serve_static_file('index.html', 'text/html')
        elif path == '/research_dashboard':
            # 研究者向けダッシュボード
            self.serve_static_file('research_dashboard.html', 'text/html')
        elif path == '/fetch':
            # 分布データを返す
            self.handle_fetch_request(parsed_path.query)
        elif path == '/health':
            # ヘルスチェック
            self.send_json_response({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()})
        elif path == '/research':
            # 研究者向け分析データ
            self.handle_research_request(parsed_path.query)
        else:
            self.send_error(404, 'Not Found')
    
    def do_POST(self):
        """POST リクエストの処理"""
        # レート制限チェック
        if not self.check_rate_limit():
            self.send_error(429, 'Too Many Requests')
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # CORS ヘッダーを設定
        self.send_cors_headers()
        
        if path == '/submit':
            self.handle_submit_request()
        elif path == '/update_saw_alt_meanings':
            self.handle_update_saw_alt_meanings()
        else:
            self.send_error(404, 'Not Found')
    
    def do_OPTIONS(self):
        """CORS プリフライトリクエストの処理"""
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        """CORS ヘッダーを送信"""
        self.send_response(200)
        # Netlifyドメインからのアクセスを許可
        origin = self.headers.get('Origin')
        allowed_origins = [
            'https://kotoimidiary.netlify.app',
            'http://localhost:8000',
            'http://127.0.0.1:8000'
        ]
        
        if origin in allowed_origins:
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            # デフォルトでNetlifyを許可
            self.send_header('Access-Control-Allow-Origin', 'https://kotoimidiary.netlify.app')
            
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        
        # セキュリティヘッダーの追加
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Content-Security-Policy', 
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
    
    def serve_static_file(self, filename, content_type):
        """静的ファイルを提供"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, 'File not found')
    
    def handle_submit_request(self):
        """データ送信リクエストを処理"""
        try:
            # リクエストボディを読み取り
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # データバリデーション
            if not self.validate_submission_data(data):
                self.send_error(400, 'Invalid data')
                return
            
            # 品質フラグの追加処理
            self.enhance_quality_flags(data)
            
            # データベースに保存
            db = DatabaseManager()
            record_id = db.insert_record(data)
            
            # 成功レスポンス
            response = {
                'success': True,
                'record_id': record_id,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            self.send_json_response(response)
            
        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON')
        except Exception as e:
            print(f"Submit error: {e}")
            self.send_error(500, 'Internal server error')
    
    def handle_update_saw_alt_meanings(self):
        """saw_alt_meaningsフラグの更新"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            record_id = data.get('record_id')
            saw_alt_meanings = data.get('saw_alt_meanings', False)
            
            if not record_id:
                self.send_error(400, 'record_id required')
                return
            
            db = DatabaseManager()
            success = db.update_saw_alt_meanings(record_id, saw_alt_meanings)
            
            if success:
                self.send_json_response({'success': True})
            else:
                self.send_error(404, 'Record not found')
                
        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON')
        except Exception as e:
            print(f"Update saw_alt_meanings error: {e}")
            self.send_error(500, 'Internal server error')
    
    def handle_research_request(self, query_string):
        """研究者向け分析データ取得リクエストを処理"""
        try:
            from research_analyzer import MeaningDiversityAnalyzer
            
            params = parse_qs(query_string)
            analysis_type = params.get('type', ['diversity'])[0]
            event_tag = params.get('event_tag', [None])[0]
            
            analyzer = MeaningDiversityAnalyzer(self.db_path if hasattr(self, 'db_path') else 'kotoiminiki.db')
            
            if analysis_type == 'diversity':
                result = analyzer.analyze_event_diversity(event_tag)
            elif analysis_type == 'mode_comparison':
                result = analyzer.compare_solo_vs_social(event_tag)
            elif analysis_type == 'revision_impact':
                result = analyzer.analyze_revision_impact(event_tag)
            elif analysis_type == 'comprehensive':
                result = analyzer.generate_comprehensive_report()
            else:
                self.send_error(400, 'Invalid analysis type')
                return
            
            self.send_json_response(result)
            
        except Exception as e:
            print(f"Research request error: {e}")
            self.send_error(500, 'Analysis error')
    
    def handle_fetch_request(self, query_string):
        """分布データ取得リクエストを処理"""
        try:
            params = parse_qs(query_string)
            event_tag = params.get('event_tag', [''])[0]
            
            if not event_tag:
                self.send_error(400, 'event_tag parameter required')
                return
            
            db = DatabaseManager()
            distribution_data = db.get_distribution_data(event_tag)
            
            self.send_json_response(distribution_data)
            
        except Exception as e:
            print(f"Fetch error: {e}")
            self.send_error(500, 'Internal server error')
    
    def sanitize_input(self, text):
        """入力値のサニタイゼーション"""
        if not isinstance(text, str):
            return str(text)
        
        # HTML エスケープ
        sanitized = html.escape(text)
        
        # 危険なスクリプトタグを除去
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)
        
        # その他の危険なタグを除去
        dangerous_tags = ['iframe', 'object', 'embed', 'form', 'input', 'button']
        for tag in dangerous_tags:
            sanitized = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)
            sanitized = re.sub(f'<{tag}[^>]*/?>', '', sanitized, flags=re.IGNORECASE)
        
        # JavaScript プロトコルを除去
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        
        # 長すぎる入力を制限(DoS攻撃対策)
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]
        
        return sanitized.strip()
    
    def validate_submission_data(self, data):
        """送信データのバリデーション(強化版)"""
        required_fields = [
            'user_id_hash', 'consent', 'mode', 'event_tag', 
            'meaning_text', 'rt_ms'
        ]
        
        # 必須フィールドの存在確認
        for field in required_fields:
            if field not in data:
                return False
        
        # データ型の検証
        if not isinstance(data['consent'], bool):
            return False
        
        if not isinstance(data['rt_ms'], int) or data['rt_ms'] < 0:
            return False
        
        # テキストフィールドのサニタイゼーション
        text_fields = ['event_text', 'meaning_text', 'meaning_tag', 'user_id_hash', 'event_tag']
        for field in text_fields:
            if field in data and data[field]:
                data[field] = self.sanitize_input(data[field])
        
        # 意味づけテキストの長さチェック
        if len(data['meaning_text'].strip()) < 5:
            return False
        
        # モードの値チェック
        if data['mode'] not in ['solo', 'social']:
            return False
        
        # event_tag の検証(許可されたタグのみ)
        allowed_event_tags = [
            'work_late', 'work_praised', 'work_failed', 'work_success', 'work_conflict',
            'relationship_fight', 'relationship_support', 'relationship_betrayal', 
            'relationship_love', 'relationship_breakup',
            'health_sick', 'health_injury', 'health_recovery', 'health_tired',
            'money_loss', 'money_gain', 'money_debt', 'money_purchase',
            'weather_rain', 'weather_storm', 'weather_sunny', 'weather_cold',
            'accident_minor', 'accident_loss', 'accident_broken', 'accident_delay',
            'achievement_goal', 'achievement_recognition', 'achievement_skill',
            'loss_opportunity', 'loss_mistake', 'loss_rejection',
            'surprise_news', 'surprise_meeting', 'surprise_discovery',
            'other'
        ]
        
        if data['event_tag'] not in allowed_event_tags:
            return False
        
        # user_id_hash の形式確認
        if not re.match(r'^anon_[a-z0-9_]+$', data['user_id_hash']):
            return False
        
        return True
    
    def enhance_quality_flags(self, data):
        """品質フラグの追加処理"""
        quality_flags = json.loads(data.get('quality_flags', '{}'))
        
        # 重複チェック
        db = DatabaseManager()
        is_duplicate = db.check_duplicate(
            data['user_id_hash'], 
            data['event_tag'], 
            data['meaning_text']
        )
        quality_flags['duplicate'] = is_duplicate
        
        # スパム検出(反応時間ベース)
        if data['rt_ms'] < 500:
            quality_flags['spam'] = True
        
        # 短すぎる意味づけ
        if len(data['meaning_text'].strip()) < 10:
            quality_flags['too_short'] = True
        
        data['quality_flags'] = json.dumps(quality_flags)
    
    def send_json_response(self, data):
        """JSON レスポンスを送信"""
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))

class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, db_path='kotoiminiki.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベースとテーブルの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # records テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY,
                user_id_hash TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                consent BOOLEAN NOT NULL,
                mode TEXT NOT NULL,
                event_text TEXT,
                event_tag TEXT NOT NULL,
                meaning_text TEXT NOT NULL,
                meaning_tag TEXT,
                rt_ms INTEGER NOT NULL,
                saw_alt_meanings BOOLEAN DEFAULT FALSE,
                changed_after_view BOOLEAN DEFAULT FALSE,
                quality_flags TEXT,
                locale TEXT DEFAULT 'ja-JP',
                original_meaning TEXT,
                revision_count INTEGER DEFAULT 0
            )
        ''')
        
        # インデックスの作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_tag ON records(event_tag)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON records(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_consent ON records(consent)')
        
        conn.commit()
        conn.close()
    
    def insert_record(self, data):
        """レコードの挿入"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # レコードIDの生成
        record_id = self.generate_record_id()
        
        cursor.execute('''
            INSERT INTO records (
                id, user_id_hash, timestamp, consent, mode,
                event_text, event_tag, meaning_text, meaning_tag,
                rt_ms, saw_alt_meanings, changed_after_view,
                quality_flags, locale, original_meaning, revision_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record_id,
            data['user_id_hash'],
            data['timestamp'],
            data['consent'],
            data['mode'],
            data.get('event_text', ''),
            data['event_tag'],
            data['meaning_text'],
            data.get('meaning_tag', ''),
            data['rt_ms'],
            data.get('saw_alt_meanings', False),
            data.get('changed_after_view', False),
            data.get('quality_flags', '{}'),
            data.get('locale', 'ja-JP'),
            data.get('original_meaning', ''),
            data.get('revision_count', 0)
        ))
        
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_distribution_data(self, event_tag):
        """分布データの取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 品質の良いデータのみを取得
        cursor.execute('''
            SELECT meaning_tag, meaning_text, quality_flags
            FROM records 
            WHERE event_tag = ? AND consent = TRUE
        ''', (event_tag,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 品質フィルタリング
        filtered_rows = []
        for row in rows:
            quality_flags = json.loads(row[2] or '{}')
            if not (quality_flags.get('spam', False) or 
                   quality_flags.get('duplicate', False)):
                filtered_rows.append(row)
        
        # 分布の計算
        distribution = {}
        meaning_texts = []
        
        for row in filtered_rows:
            meaning_tag = row[0] if row[0] else 'その他'
            meaning_text = row[1]
            
            # タグが複数ある場合は分割
            tags = meaning_tag.split(',') if meaning_tag else ['その他']
            for tag in tags:
                tag = tag.strip()
                if tag:
                    distribution[tag] = distribution.get(tag, 0) + 1
            
            meaning_texts.append(meaning_text)
        
        # 代表的な意味づけをランダムサンプリング
        import random
        sample_size = min(3, len(meaning_texts))
        sample_meanings = random.sample(meaning_texts, sample_size) if meaning_texts else []
        
        return {
            'distribution': distribution,
            'samples': sample_meanings,
            'total_count': len(filtered_rows)
        }
    
    def check_duplicate(self, user_id_hash, event_tag, meaning_text):
        """重複チェック"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 同じユーザーが同じ出来事カテゴリで似た意味づけをしているかチェック
        cursor.execute('''
            SELECT COUNT(*) FROM records 
            WHERE user_id_hash = ? AND event_tag = ? 
            AND meaning_text = ?
            AND timestamp > datetime('now', '-1 day')
        ''', (user_id_hash, event_tag, meaning_text))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def generate_record_id(self):
        """レコードIDの生成"""
        timestamp = str(int(time.time() * 1000))
        random_part = hashlib.md5(os.urandom(32)).hexdigest()[:8]
        return f"rec_{timestamp}_{random_part}"
    
    def update_saw_alt_meanings(self, record_id, saw_alt_meanings):
        """saw_alt_meaningsフラグの更新"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE records 
            SET saw_alt_meanings = ?
            WHERE id = ?
        ''', (saw_alt_meanings, record_id))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0

def run_server(port=8000, host='localhost'):
    """サーバーの起動"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, MeaningDiversityServer)
    
    # Railway用のキープアライブ設定
    httpd.timeout = None  # タイムアウトを無効化
    
    print(f"ことイミ日記サーバーを起動しました")
    print(f"URL: http://{host}:{port}")
    print(f"データベース: kotoiminiki.db")
    print("Ctrl+C で停止できます")
    
    try:
        print("サーバーをキープアライブモードで開始...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しています...")
        httpd.server_close()
        print("サーバーが停止しました")

if __name__ == '__main__':
    import sys
    
    # コマンドライン引数の処理
    port = int(os.environ.get('PORT', 8000))  # Railway用の環境変数対応
    host = '0.0.0.0'  # Railway用にすべてのアドレスでリッスン
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("ポート番号は数値で指定してください")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    # データベースの初期化
    db = DatabaseManager()
    print("データベースを初期化しました")
    
    # サーバーの起動
    run_server(port, host)