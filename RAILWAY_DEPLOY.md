# ことイミ日記 - Railway デプロイガイド

## 🚀 Railway デプロイ手順

### 1. Railway アカウント作成
1. [Railway](https://railway.app/) にアクセス
2. GitHub アカウントでサインアップ

### 2. プロジェクトをデプロイ
1. Railway ダッシュボードで "New Project" をクリック
2. "Deploy from GitHub repo" を選択
3. このリポジトリ (`imizuke`) を選択
4. 自動的にデプロイが開始されます

### 3. 環境変数設定（必要に応じて）
- `PORT`: 自動設定されます
- `ALLOWED_ORIGIN`: Netlify URLが自動設定されます

### 4. デプロイ完了後
1. Railway から提供されるURLをコピー（例: `https://your-app-name.railway.app`）
2. index.html の `API_BASE_URL` を更新:
   ```javascript
   const API_BASE_URL = 'https://your-app-name.railway.app';
   ```
3. research_dashboard.html の `API_BASE_URL` も同様に更新
4. Netlify に再デプロイ

### 5. 動作確認
- フロントエンド: https://kotoimidiary.netlify.app/
- バックエンド: https://your-app-name.railway.app/
- 研究ダッシュボード: https://kotoimidiary.netlify.app/research_dashboard.html

## 📝 備考
- Railway は自動的にPythonを検出し、適切な環境を構築します
- SQLiteデータベースは自動的に作成されます
- CORS設定により、Netlifyからのアクセスが許可されています

## 🔧 トラブルシューティング
1. **デプロイエラー**: ログを確認し、requirements.txtが正しいことを確認
2. **CORS エラー**: server.pyのallowed_originsリストを確認
3. **データベースエラー**: Railway上でSQLiteファイルが作成されているか確認