# ことイミ日記 (Meaning Diversity Logger)

出来事の意味づけを記録し、多様性を探求するWebアプリケーションです。

## 特徴

- **軽量・依存最小**: npm、Supabase、Firebase等の外部依存なし
- **プライバシー重視**: 研究協力の選択可能、匿名化データのみ
- **2つのモード**: 
  - **Solo**: 純粋に個人の記録のみ
  - **Social**: 他者の意味づけ分布も閲覧可能
- **美しいUI/UX**: モダンでレスポンシブなデザイン

## 技術仕様

### フロントエンド
- 純粋な HTML/CSS/JavaScript（外部ライブラリなし）
- SVG/Canvas での自前グラフ描画
- LocalStorage でのオフライン対応

### サーバーサイド  
- Python 標準ライブラリのみ使用
- SQLite データベース
- RESTful API (/submit, /fetch)

## クイックスタート

### 1. サーバー起動

```bash
# デフォルト (localhost:8000)
python server.py

# カスタムポート
python server.py 8080

# 外部アクセス許可
python server.py 8000 0.0.0.0
```

### 2. ブラウザでアクセス

```
http://localhost:8000
```

## データ構造

### records テーブル
- `id`: レコードID (主キー)
- `user_id_hash`: 匿名化ユーザーID
- `timestamp`: 記録時刻
- `consent`: 研究協力同意フラグ
- `mode`: solo/social
- `event_text`: 出来事（自由記述）
- `event_tag`: 出来事カテゴリ
- `meaning_text`: 意味づけ（自由記述）
- `meaning_tag`: 意味づけタグ
- `rt_ms`: 反応時間（ミリ秒）
- `quality_flags`: 品質管理情報

## API仕様

### POST /submit
記録データの送信

```json
{
  "user_id_hash": "user_abc123",
  "timestamp": "2025-09-21T10:30:00Z",
  "consent": true,
  "mode": "social",
  "event_tag": "work",
  "event_text": "プレゼンで失敗した",
  "meaning_text": "次に活かせる良い経験になった",
  "meaning_tag": "learning,growth",
  "rt_ms": 2500
}
```

### GET /fetch?event_tag=work
分布データの取得

```json
{
  "distribution": {
    "learning": 15,
    "negative": 8,
    "growth": 12
  },
  "samples": [
    "失敗から学べることがたくさんあった",
    "次回はもっと準備をしよう",
    "経験値が上がった"
  ],
  "total_count": 35
}
```

## データ品質管理

- **too_short**: 意味づけ文字数 < 10文字
- **spam**: 反応時間 < 500ms
- **duplicate**: 24時間以内の同一内容

## プライバシー・倫理

- 個人情報は一切収集しない
- ユーザーIDは匿名化ハッシュ
- 研究協力は完全に任意
- データ削除請求には対応不可（匿名化のため）

## 研究活用

### 多様性指標
- エントロピー計算
- 意味埋め込み距離分析
- 合意率測定

### モード比較
- Solo vs Social の分布差
- 他者情報提示による影響分析

## トラブルシューティング

### サーバーが起動しない
- ポートが使用中の場合は別のポート番号を指定
- `python --version` で Python 3.6+ を確認

### データベースエラー
- `kotoiminiki.db` ファイルの権限を確認
- SQLite3 がインストールされているか確認

### ブラウザでアクセスできない
- ファイアウォール設定を確認
- `localhost` の代わりに `127.0.0.1` を試す

## ライセンス

研究・教育目的での利用を想定。
商用利用の場合は別途相談。

## 開発者

ことイミ日記プロジェクト  
Meaning Diversity Logger System