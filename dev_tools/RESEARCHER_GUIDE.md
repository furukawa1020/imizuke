# 研究者向けデータアクセスガイド

## 🔬 研究データの確認方法

### 1. **Webダッシュボード（最も簡単）**
```
http://localhost:8000/research_dashboard
```
- リアルタイム分析
- 視覚的なグラフとチャート
- 多様性指標の自動計算
- モード比較分析

### 2. **コマンドライン分析ツール**
```bash
cd "c:\Users\wakuw\OneDrive\画像\デスクトップ\.vscode\imizuke"
python dev_tools/research_data_analyzer.py
```

### 3. **直接データベースアクセス**
```bash
sqlite3 kotoiminiki.db
```

## 📊 データベース構造

### メインテーブル: `records`
```sql
-- 基本フィールド
id                  -- レコードID
user_id_hash        -- 匿名化ユーザーID
timestamp          -- 記録時刻
consent            -- 研究同意フラグ（TRUE/FALSE）
mode               -- 利用モード（'solo'/'social'）

-- 記録内容
event_tag          -- 出来事カテゴリ
event_text         -- 出来事詳細（任意）
meaning_text       -- 意味づけ内容
meaning_tag        -- 意味づけタグ

-- 研究用メタデータ
rt_ms              -- 反応時間（ミリ秒）
saw_alt_meanings   -- 他者データ閲覧フラグ
changed_after_view -- 閲覧後変更フラグ
quality_flags      -- データ品質フラグ（JSON）
original_meaning   -- 変更前の意味づけ
revision_count     -- 修正回数
```

## 🔍 よく使うSQLクエリ

### 基本統計
```sql
-- 同意データの件数
SELECT COUNT(*) FROM records WHERE consent = TRUE;

-- モード別分布
SELECT mode, COUNT(*) FROM records 
WHERE consent = TRUE 
GROUP BY mode;

-- 出来事別分布
SELECT event_tag, COUNT(*) FROM records 
WHERE consent = TRUE 
GROUP BY event_tag 
ORDER BY COUNT(*) DESC;
```

### 品質分析
```sql
-- 高品質データ（品質問題なし）
SELECT COUNT(*) FROM records 
WHERE consent = TRUE 
AND quality_flags = '{}';

-- 反応時間統計
SELECT 
    AVG(rt_ms) as avg_time,
    MIN(rt_ms) as min_time,
    MAX(rt_ms) as max_time
FROM records 
WHERE consent = TRUE;
```

### 多様性分析
```sql
-- 出来事ごとの意味づけの多様性
SELECT 
    event_tag,
    COUNT(*) as total_records,
    COUNT(DISTINCT meaning_text) as unique_meanings,
    ROUND(
        CAST(COUNT(DISTINCT meaning_text) AS FLOAT) / COUNT(*) * 100, 2
    ) as diversity_percentage
FROM records 
WHERE consent = TRUE 
GROUP BY event_tag
HAVING COUNT(*) >= 5
ORDER BY diversity_percentage DESC;
```

### 社会的影響分析
```sql
-- 他者データ閲覧の影響
SELECT 
    COUNT(*) as total_social,
    SUM(CASE WHEN saw_alt_meanings THEN 1 ELSE 0 END) as saw_others,
    SUM(CASE WHEN changed_after_view THEN 1 ELSE 0 END) as changed_after,
    ROUND(
        CAST(SUM(CASE WHEN changed_after_view THEN 1 ELSE 0 END) AS FLOAT) /
        SUM(CASE WHEN saw_alt_meanings THEN 1 ELSE 0 END) * 100, 2
    ) as change_rate_percent
FROM records 
WHERE consent = TRUE AND mode = 'social';
```

## 📈 研究分析項目

### 1. 多様性指標
- **エントロピー H(E)**: 意味づけの多様性
- **合意率 max p(M_i|E)**: 最も多い意味づけの割合
- **意味距離**: テキスト間の類似度

### 2. モード比較
- Solo vs Social の分布差
- 社会的情報の影響度
- 認知バイアスの検出

### 3. 認知変化分析
- 他者情報提示前後の変化
- 修正パターンの分析
- メタ認知効果の測定

## 🚀 クイックスタート

1. **まずはダッシュボードで概要確認**
   ```
   http://localhost:8000/research_dashboard
   ```

2. **詳細分析が必要な場合**
   ```bash
   python dev_tools/research_data_analyzer.py
   ```

3. **カスタム分析**
   ```bash
   sqlite3 kotoiminiki.db
   .schema records
   SELECT * FROM records LIMIT 5;
   ```

4. **データエクスポート**
   - 分析ツールでCSV出力
   - Excel/R/Python で外部分析

## ⚠️ 研究倫理の遵守

- `consent = TRUE` のデータのみ研究利用
- 個人特定可能情報は含まれていない
- user_id_hash は強力に匿名化済み
- 外部発表時は追加の匿名化処理を推奨

最終更新: 2025-09-21