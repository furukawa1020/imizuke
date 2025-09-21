# セキュリティ強化ガイド

## 🔒 実装済みのセキュリティ対策

### ✅ 完了済み
- **CORS設定の厳格化** - 特定ドメインのみ許可
- **セキュリティヘッダー** - CSP, X-Frame-Options, X-XSS-Protection等
- **入力値サニタイゼーション** - HTML/Script injection対策
- **SQLインジェクション対策** - パラメータ化クエリ使用
- **レート制限** - 1分間30リクエスト、5分間ブロック

### 📊 セキュリティ設定詳細

#### 1. CORS設定
```
Access-Control-Allow-Origin: 環境変数ALLOWED_ORIGINで制御
デフォルト: http://localhost:8000
本番: 実際のドメインを設定
```

#### 2. セキュリティヘッダー
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: 厳格なポリシー設定
```

#### 3. レート制限
```
通常リクエスト: 1分間30回まで
制限時間: 5分間ブロック
対象: POST /submit主要エンドポイント
```

#### 4. 入力値検証
```
HTMLエスケープ: 全テキストフィールド
危険タグ除去: script, iframe, object等
文字数制限: 最大10,000文字
許可event_tag: 事前定義リストのみ
```

## 🚨 本番運用前の必須設定

### 1. 環境変数設定
```bash
# CORS許可ドメイン
export ALLOWED_ORIGIN="https://yourdomain.com"

# SSL証明書（推奨）
export SSL_CERT_PATH="/path/to/cert.pem"
export SSL_KEY_PATH="/path/to/key.pem"
```

### 2. ファイアウォール設定
```bash
# 必要ポートのみ開放
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 22    # SSH (管理用)
sudo ufw enable
```

### 3. データベースセキュリティ
```bash
# データベースファイル権限設定
chmod 600 kotoiminiki.db
chown www-data:www-data kotoiminiki.db

# バックアップの暗号化
gpg --cipher-algo AES256 --compress-algo 1 --symmetric kotoiminiki.db
```

## ⚠️ 追加考慮事項

### 1. 高負荷対策
- リバースプロキシ（nginx）の使用を推奨
- 静的ファイルの配信分離
- データベース接続プールの実装

### 2. ログ監視
```python
# アクセスログの記録
import logging
logging.basicConfig(
    filename='access.log',
    level=logging.INFO,
    format='%(asctime)s %(remote_addr)s %(request_line)s %(status_code)s'
)
```

### 3. 定期セキュリティチェック
- 依存ライブラリの脆弱性スキャン
- アクセスログの異常検知
- データベース整合性チェック

## 🛡️ セキュリティレベル評価

| 項目 | レベル | 状態 |
|------|--------|------|
| 入力値検証 | ★★★★☆ | 強化済み |
| 認証・認可 | N/A | 匿名システム |
| データ暗号化 | ★★★☆☆ | ハッシュ化済み |
| 通信暗号化 | ★★☆☆☆ | HTTP/HTTPS対応 |
| レート制限 | ★★★★☆ | 実装済み |
| ログ監視 | ★★☆☆☆ | 基本的な実装 |

## 📝 セキュリティ監査チェックリスト

### 導入前チェック
- [ ] CORS設定の確認
- [ ] セキュリティヘッダーの動作確認
- [ ] レート制限の動作テスト
- [ ] 入力値検証の境界値テスト
- [ ] SQLインジェクション耐性テスト

### 運用中チェック（月次）
- [ ] アクセスログの異常チェック
- [ ] レート制限の発動状況確認
- [ ] データベースサイズの監視
- [ ] セキュリティアップデートの適用
- [ ] バックアップの整合性確認

### インシデント対応
1. **不正アクセス検知時**
   - 該当IPのブロック
   - ログの詳細分析
   - 必要に応じてサービス一時停止

2. **データ改ざん検知時**
   - バックアップからの復旧
   - 脆弱性の特定と修正
   - 影響範囲の調査

3. **DoS攻撃検知時**
   - レート制限の強化
   - CDN/プロキシでの対策
   - 攻撃元IPの報告

最終更新: 2025-01-27