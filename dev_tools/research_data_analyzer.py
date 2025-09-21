#!/usr/bin/env python3
"""
研究者向けデータ分析コマンドラインツール
データベースから直接研究データを取得・分析
"""

import sqlite3
import json
import datetime
from collections import Counter, defaultdict
import statistics

class ResearchDataAnalyzer:
    """研究データ分析クラス"""
    
    def __init__(self, db_path='kotoiminiki.db'):
        self.db_path = db_path
    
    def get_basic_stats(self):
        """基本統計情報を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 全データ数
        cursor.execute("SELECT COUNT(*) FROM records")
        total_records = cursor.fetchone()[0]
        
        # 同意データ数
        cursor.execute("SELECT COUNT(*) FROM records WHERE consent = TRUE")
        consented_records = cursor.fetchone()[0]
        
        # モード別集計
        cursor.execute("SELECT mode, COUNT(*) FROM records WHERE consent = TRUE GROUP BY mode")
        mode_stats = dict(cursor.fetchall())
        
        # 出来事別集計
        cursor.execute("SELECT event_tag, COUNT(*) FROM records WHERE consent = TRUE GROUP BY event_tag ORDER BY COUNT(*) DESC")
        event_stats = cursor.fetchall()
        
        # 日別データ数
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) 
            FROM records WHERE consent = TRUE 
            GROUP BY DATE(timestamp) 
            ORDER BY date DESC 
            LIMIT 7
        """)
        daily_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_records': total_records,
            'consented_records': consented_records,
            'consent_rate': consented_records / total_records if total_records > 0 else 0,
            'mode_distribution': mode_stats,
            'event_distribution': event_stats,
            'daily_records': daily_stats
        }
    
    def get_quality_analysis(self):
        """データ品質分析"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 品質フラグ分析
        cursor.execute("SELECT quality_flags FROM records WHERE consent = TRUE")
        quality_data = []
        
        for row in cursor.fetchall():
            flags = json.loads(row[0] or '{}')
            quality_data.append(flags)
        
        # 各品質問題の集計
        quality_issues = {
            'spam': sum(1 for q in quality_data if q.get('spam', False)),
            'duplicate': sum(1 for q in quality_data if q.get('duplicate', False)),
            'too_short': sum(1 for q in quality_data if q.get('too_short', False)),
            'high_quality': sum(1 for q in quality_data if not any(q.values()))
        }
        
        # 反応時間分析
        cursor.execute("SELECT rt_ms FROM records WHERE consent = TRUE")
        reaction_times = [row[0] for row in cursor.fetchall()]
        
        rt_stats = {}
        if reaction_times:
            rt_stats = {
                'mean': statistics.mean(reaction_times),
                'median': statistics.median(reaction_times),
                'min': min(reaction_times),
                'max': max(reaction_times),
                'std': statistics.stdev(reaction_times) if len(reaction_times) > 1 else 0
            }
        
        conn.close()
        
        return {
            'quality_issues': quality_issues,
            'reaction_time_stats': rt_stats,
            'total_analyzed': len(quality_data)
        }
    
    def get_meaning_diversity_analysis(self):
        """意味づけの多様性分析"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 出来事ごとの意味づけ分析
        cursor.execute("""
            SELECT event_tag, meaning_text, meaning_tag 
            FROM records 
            WHERE consent = TRUE
        """)
        
        event_meanings = defaultdict(list)
        for event_tag, meaning_text, meaning_tag in cursor.fetchall():
            event_meanings[event_tag].append({
                'text': meaning_text,
                'tags': meaning_tag.split(',') if meaning_tag else []
            })
        
        # 各出来事の多様性計算
        diversity_results = {}
        for event_tag, meanings in event_meanings.items():
            if len(meanings) < 2:
                continue
                
            # 意味づけテキストの多様性（ユニーク率）
            texts = [m['text'] for m in meanings]
            unique_texts = len(set(texts))
            diversity_rate = unique_texts / len(texts)
            
            # タグの多様性
            all_tags = []
            for m in meanings:
                all_tags.extend([tag.strip() for tag in m['tags'] if tag.strip()])
            
            tag_diversity = len(set(all_tags)) / len(all_tags) if all_tags else 0
            
            diversity_results[event_tag] = {
                'total_meanings': len(meanings),
                'unique_meanings': unique_texts,
                'diversity_rate': diversity_rate,
                'tag_diversity': tag_diversity,
                'sample_meanings': texts[:3]
            }
        
        conn.close()
        
        return diversity_results
    
    def get_social_impact_analysis(self):
        """社会的影響分析（他者データ閲覧の影響）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Social モードで他者データを見た人の分析
        cursor.execute("""
            SELECT saw_alt_meanings, changed_after_view, original_meaning, meaning_text
            FROM records 
            WHERE consent = TRUE AND mode = 'social'
        """)
        
        social_data = cursor.fetchall()
        
        total_social = len(social_data)
        saw_alternatives = sum(1 for row in social_data if row[0])  # saw_alt_meanings
        changed_after = sum(1 for row in social_data if row[1])     # changed_after_view
        
        # 変更例
        change_examples = []
        for row in social_data:
            if row[1] and row[2] and row[3]:  # changed_after_view and both texts
                change_examples.append({
                    'original': row[2],
                    'revised': row[3]
                })
        
        conn.close()
        
        return {
            'total_social_users': total_social,
            'saw_alternatives': saw_alternatives,
            'changed_after_viewing': changed_after,
            'change_rate': changed_after / saw_alternatives if saw_alternatives > 0 else 0,
            'influence_rate': saw_alternatives / total_social if total_social > 0 else 0,
            'change_examples': change_examples[:5]  # 最初の5例
        }
    
    def export_research_data(self, filename=None):
        """研究データをCSV形式でエクスポート"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_data_{timestamp}.csv"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, timestamp, mode, event_tag, event_text,
                meaning_text, meaning_tag, rt_ms,
                saw_alt_meanings, changed_after_view,
                quality_flags, original_meaning, revision_count
            FROM records 
            WHERE consent = TRUE
            ORDER BY timestamp
        """)
        
        import csv
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # ヘッダー
            writer.writerow([
                'record_id', 'timestamp', 'mode', 'event_tag', 'event_text',
                'meaning_text', 'meaning_tag', 'reaction_time_ms',
                'saw_alternatives', 'changed_after_view',
                'quality_flags', 'original_meaning', 'revision_count'
            ])
            
            # データ
            for row in cursor.fetchall():
                writer.writerow(row)
        
        conn.close()
        
        return filename

def main():
    """メイン実行関数"""
    print("=" * 60)
    print("ことイミ日記 - 研究者向けデータ分析ツール")
    print("=" * 60)
    
    analyzer = ResearchDataAnalyzer()
    
    try:
        print("\n📊 基本統計情報")
        print("-" * 40)
        basic_stats = analyzer.get_basic_stats()
        print(f"総記録数: {basic_stats['total_records']}")
        print(f"研究同意データ: {basic_stats['consented_records']}")
        print(f"同意率: {basic_stats['consent_rate']:.1%}")
        print(f"モード分布: {basic_stats['mode_distribution']}")
        
        print("\n🔍 データ品質分析")
        print("-" * 40)
        quality_stats = analyzer.get_quality_analysis()
        print(f"高品質データ: {quality_stats['quality_issues']['high_quality']}")
        print(f"スパム検出: {quality_stats['quality_issues']['spam']}")
        print(f"重複検出: {quality_stats['quality_issues']['duplicate']}")
        print(f"短文検出: {quality_stats['quality_issues']['too_short']}")
        
        if quality_stats['reaction_time_stats']:
            rt = quality_stats['reaction_time_stats']
            print(f"平均反応時間: {rt['mean']:.0f}ms")
            print(f"中央値反応時間: {rt['median']:.0f}ms")
        
        print("\n🌈 意味づけ多様性分析")
        print("-" * 40)
        diversity_analysis = analyzer.get_meaning_diversity_analysis()
        for event, stats in list(diversity_analysis.items())[:5]:  # 上位5つ
            print(f"\n{event}:")
            print(f"  記録数: {stats['total_meanings']}")
            print(f"  多様性率: {stats['diversity_rate']:.1%}")
            print(f"  例: {stats['sample_meanings'][0][:30]}..." if stats['sample_meanings'] else "  例: なし")
        
        print("\n👥 社会的影響分析")
        print("-" * 40)
        social_impact = analyzer.get_social_impact_analysis()
        print(f"Socialモード利用者: {social_impact['total_social_users']}")
        print(f"他者データ閲覧者: {social_impact['saw_alternatives']}")
        print(f"閲覧後変更者: {social_impact['changed_after_viewing']}")
        print(f"変更率: {social_impact['change_rate']:.1%}")
        print(f"影響率: {social_impact['influence_rate']:.1%}")
        
        # データエクスポート
        print("\n💾 データエクスポート")
        print("-" * 40)
        export_choice = input("研究データをCSVでエクスポートしますか？ (y/n): ").lower().strip()
        
        if export_choice == 'y':
            filename = analyzer.export_research_data()
            print(f"✅ データを {filename} にエクスポートしました")
        
        print("\n" + "=" * 60)
        print("🎯 研究分析完了")
        print("\n📋 推奨事項:")
        print("• Webダッシュボード: http://localhost:8000/research_dashboard")
        print("• API アクセス: http://localhost:8000/research?type=comprehensive")
        print("• 詳細分析: 追加のSQLクエリでカスタム分析可能")
        
    except Exception as e:
        print(f"❌ 分析エラー: {e}")
        print("データベースファイルが存在し、サーバーが停止していることを確認してください")

if __name__ == '__main__':
    main()