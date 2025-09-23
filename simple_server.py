#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """GET リクエストの処理"""
        # CORS設定
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        
        # ヘルスチェック
        self.wfile.write(b'Railway Server Running - OK')

    def do_POST(self):
        """POST リクエストの処理"""
        # CORS設定
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        
        # 簡単なレスポンス
        response = {"status": "success", "message": "POST received"}
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        """OPTIONS リクエストの処理 (CORS プリフライト)"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    # Railway環境変数取得
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    
    print(f"Starting server on {host}:{port}")
    
    # サーバー起動
    httpd = HTTPServer((host, port), SimpleHandler)
    
    try:
        print("Server is running...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")
        httpd.server_close()