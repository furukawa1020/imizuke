#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import datetime
import hashlib

class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, db_path="kotoiminiki.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベースの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # meanings テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meanings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_description TEXT NOT NULL,
                personal_meaning TEXT NOT NULL,
                context_situation TEXT,
                emotional_response TEXT,
                event_category TEXT,
                meaning_tags TEXT,
                mode TEXT DEFAULT 'solo',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # research_logs テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT NOT NULL,
                parameters TEXT,
                result_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

class MeaningDiversityAnalyzer:
    """意味づけデータの分析クラス"""
    
    def __init__(self, db_path="kotoiminiki.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """データベース接続を取得"""
        return sqlite3.connect(self.db_path)
    
    def analyze_event_diversity(self):
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
                "tag_distribution": tag_counts
            }
        finally:
            conn.close()

class APIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db_manager = DatabaseManager()
        self.analyzer = MeaningDiversityAnalyzer()
        super().__init__(*args, **kwargs)
    
    def send_cors_headers(self):
        """CORS ヘッダーを送信"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        """OPTIONS リクエストの処理 (CORS プリフライト)"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """GET リクエストの処理"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # CORS ヘッダーを設定
        self.send_response(200)
        self.send_cors_headers()
        
        if path == '/':
            # ヘルスチェック
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'Railway Server Running - OK')
            
        elif path == '/api/entries':
            # エントリ一覧取得
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM meanings ORDER BY created_at DESC LIMIT 100")
            rows = cursor.fetchall()
            
            entries = []
            for row in rows:
                entries.append({
                    "id": row[0],
                    "event_description": row[1],
                    "personal_meaning": row[2],
                    "context_situation": row[3],
                    "emotional_response": row[4],
                    "event_category": row[5],
                    "meaning_tags": row[6],
                    "mode": row[7],
                    "created_at": row[8]
                })
            
            conn.close()
            
            response = {"status": "success", "entries": entries}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        elif path == '/api/clear':
            # 管理者用：テストデータクリアエンドポイント
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meanings")
            cursor.execute("DELETE FROM research_logs")
            conn.commit()
            conn.close()
            
            response = {"status": "success", "message": "全データをクリアしました"}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        elif path == '/api/analysis':
            # 分析データ取得
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            analysis = self.analyzer.analyze_event_diversity()
            self.wfile.write(json.dumps(analysis, ensure_ascii=False).encode('utf-8'))
            
        else:
            # 404 エラー
            self.send_response(404)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            error = {"status": "error", "message": "Not Found"}
            self.wfile.write(json.dumps(error, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        """POST リクエストの処理"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # リクエストボディ読み取り
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            error = {"status": "error", "message": "Invalid JSON"}
            self.wfile.write(json.dumps(error, ensure_ascii=False).encode('utf-8'))
            return
        
        if path == '/api/entries':
            # 新しいエントリを保存
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO meanings (
                    event_description, personal_meaning, context_situation,
                    emotional_response, event_category, meaning_tags, mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('event_description', ''),
                data.get('personal_meaning', ''),
                data.get('context_situation', ''),
                data.get('emotional_response', ''),
                data.get('event_category', ''),
                data.get('meaning_tags', ''),
                data.get('mode', 'solo')
            ))
            
            conn.commit()
            entry_id = cursor.lastrowid
            conn.close()
            
            response = {"status": "success", "id": entry_id, "message": "エントリが保存されました"}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        else:
            # 404 エラー
            self.send_response(404)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            error = {"status": "error", "message": "Not Found"}
            self.wfile.write(json.dumps(error, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    # Railway環境変数取得
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    
    print(f"Starting server on {host}:{port}")
    print("Database initialized...")
    
    # サーバー起動
    httpd = HTTPServer((host, port), APIHandler)
    
    try:
        print("Server is running...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")
        httpd.server_close()