# 開発者向け技術仕様

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

## 研究者向けAPI

### GET /research?type=diversity
多様性分析データの取得

### GET /research?type=mode_comparison  
モード間比較分析

### GET /research?type=revision_impact
認知変化分析

## データベーススキーマ

```sql
CREATE TABLE records (
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
);
```

## データ品質管理

- **too_short**: 意味づけ文字数 < 10文字
- **spam**: 反応時間 < 500ms
- **duplicate**: 24時間以内の同一内容

## トラブルシューティング

### サーバーが起動しない
- ポートが使用中の場合は別のポート番号を指定
- `python --version` で Python 3.6+ を確認

### データベースエラー
- `kotoiminiki.db` ファイルの権限を確認
- SQLite3 がインストールされているか確認