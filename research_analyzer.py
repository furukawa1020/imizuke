#!/usr/bin/env python3
"""
ことイミ日記 - 研究者向け分析ツール
意味づけの多様性分析と認知パターン研究のためのデータ分析モジュール
"""

import json
import sqlite3
import math
from collections import Counter, defaultdict
import statistics

class MeaningDiversityAnalyzer:
    """意味づけ多様性分析クラス"""
    
    def __init__(self, db_path='kotoiminiki.db'):
        self.db_path = db_path
    
    def get_high_quality_data(self, event_tag=None, mode=None):
        """品質の高いデータのみを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_conditions = ["consent = TRUE"]
        params = []
        
        if event_tag:
            where_conditions.append("event_tag = ?")
            params.append(event_tag)
        
        if mode:
            where_conditions.append("mode = ?")
            params.append(mode)
        
        query = f'''
            SELECT * FROM records 
            WHERE {" AND ".join(where_conditions)}
        '''
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # 品質フィルタリング
        filtered_data = []
        for row in rows:
            quality_flags = json.loads(row[12] or '{}')  # quality_flags
            if not (quality_flags.get('spam', False) or 
                   quality_flags.get('duplicate', False)):
                filtered_data.append(row)
        
        return filtered_data
    
    def calculate_entropy(self, meanings):
        """エントロピー H(E) の計算"""
        if not meanings:
            return 0
        
        # 意味づけの頻度を計算
        meaning_counts = Counter(meanings)
        total = len(meanings)
        
        # エントロピー計算
        entropy = 0
        for count in meaning_counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def calculate_tag_entropy(self, meaning_tags):
        """タグベースのエントロピー計算"""
        if not meaning_tags:
            return 0
        
        # タグを展開
        all_tags = []
        for tag_string in meaning_tags:
            if tag_string:
                tags = [t.strip() for t in tag_string.split(',')]
                all_tags.extend(tags)
        
        return self.calculate_entropy(all_tags)
    
    def calculate_semantic_distance_avg(self, meanings):
        """意味埋め込み距離の平均（簡易版）"""
        if len(meanings) < 2:
            return 0
        
        # 簡易的な文字ベース類似度計算
        distances = []
        for i in range(len(meanings)):
            for j in range(i + 1, len(meanings)):
                distance = self.simple_text_distance(meanings[i], meanings[j])
                distances.append(distance)
        
        return statistics.mean(distances) if distances else 0
    
    def simple_text_distance(self, text1, text2):
        """簡易テキスト距離計算（レーベンシュタイン距離の正規化版）"""
        def levenshtein_distance(s1, s2):
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        distance = levenshtein_distance(text1.lower(), text2.lower())
        max_len = max(len(text1), len(text2))
        return distance / max_len if max_len > 0 else 0
    
    def calculate_consensus_rate(self, meaning_tags):
        """合意率 max p(M_i|E) の計算"""
        if not meaning_tags:
            return 0
        
        # タグごとの出現回数を計算
        tag_counts = defaultdict(int)
        total_entries = len(meaning_tags)
        
        for tag_string in meaning_tags:
            if tag_string:
                tags = [t.strip() for t in tag_string.split(',')]
                for tag in tags:
                    if tag:
                        tag_counts[tag] += 1
        
        # 最大出現率を計算
        if not tag_counts:
            return 0
        
        max_count = max(tag_counts.values())
        return max_count / total_entries
    
    def analyze_event_diversity(self, event_tag):
        """出来事ごとの多様性指標分析"""
        data = self.get_high_quality_data(event_tag=event_tag)
        
        meanings = [row[7] for row in data]  # meaning_text
        meaning_tags = [row[8] for row in data]  # meaning_tag
        
        analysis = {
            'event_tag': event_tag,
            'total_entries': len(data),
            'entropy_text': self.calculate_entropy(meanings),
            'entropy_tags': self.calculate_tag_entropy(meaning_tags),
            'semantic_distance_avg': self.calculate_semantic_distance_avg(meanings),
            'consensus_rate': self.calculate_consensus_rate(meaning_tags),
            'sample_meanings': meanings[:5] if meanings else []
        }
        
        return analysis
    
    def compare_solo_vs_social(self, event_tag=None):
        """Solo vs Social モード比較分析"""
        solo_data = self.get_high_quality_data(event_tag=event_tag, mode='solo')
        social_data = self.get_high_quality_data(event_tag=event_tag, mode='social')
        
        solo_meanings = [row[7] for row in solo_data]
        social_meanings = [row[7] for row in social_data]
        solo_tags = [row[8] for row in solo_data]
        social_tags = [row[8] for row in social_data]
        
        comparison = {
            'event_tag': event_tag or 'all',
            'solo': {
                'count': len(solo_data),
                'entropy_text': self.calculate_entropy(solo_meanings),
                'entropy_tags': self.calculate_tag_entropy(solo_tags),
                'consensus_rate': self.calculate_consensus_rate(solo_tags)
            },
            'social': {
                'count': len(social_data),
                'entropy_text': self.calculate_entropy(social_meanings),
                'entropy_tags': self.calculate_tag_entropy(social_tags),
                'consensus_rate': self.calculate_consensus_rate(social_tags)
            }
        }
        
        # 差分計算
        comparison['differences'] = {
            'entropy_text_diff': comparison['social']['entropy_text'] - comparison['solo']['entropy_text'],
            'entropy_tags_diff': comparison['social']['entropy_tags'] - comparison['solo']['entropy_tags'],
            'consensus_rate_diff': comparison['social']['consensus_rate'] - comparison['solo']['consensus_rate']
        }
        
        return comparison
    
    def analyze_revision_impact(self, event_tag=None):
        """他者結果表示後の変化分析（changed_after_view）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_conditions = [
            "consent = TRUE", 
            "mode = 'social'", 
            "saw_alt_meanings = TRUE"
        ]
        params = []
        
        if event_tag:
            where_conditions.append("event_tag = ?")
            params.append(event_tag)
        
        query = f'''
            SELECT meaning_text, changed_after_view, original_meaning, revision_count
            FROM records 
            WHERE {" AND ".join(where_conditions)}
        '''
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # 変更率の計算
        total_saw_alt = len(rows)
        changed_count = sum(1 for row in rows if row[1])  # changed_after_view
        
        revision_analysis = {
            'event_tag': event_tag or 'all',
            'total_saw_alt_meanings': total_saw_alt,
            'changed_after_view_count': changed_count,
            'change_rate': changed_count / total_saw_alt if total_saw_alt > 0 else 0,
            'revisions': []
        }
        
        # 具体的な変更例
        for row in rows:
            if row[1] and row[2]:  # changed_after_view and original_meaning
                revision_analysis['revisions'].append({
                    'original': row[2],
                    'revised': row[0],
                    'revision_count': row[3]
                })
        
        return revision_analysis
    
    def generate_comprehensive_report(self):
        """包括的な分析レポート生成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 出来事タグ一覧取得
        cursor.execute('''
            SELECT DISTINCT event_tag 
            FROM records 
            WHERE consent = TRUE
        ''')
        event_tags = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        report = {
            'generated_at': datetime.datetime.now().isoformat(),
            'summary': {
                'total_event_types': len(event_tags),
                'event_analyses': [],
                'mode_comparisons': [],
                'revision_analyses': []
            }
        }
        
        # 各出来事の分析
        for event_tag in event_tags:
            event_analysis = self.analyze_event_diversity(event_tag)
            report['summary']['event_analyses'].append(event_analysis)
            
            # モード比較
            mode_comparison = self.compare_solo_vs_social(event_tag)
            report['summary']['mode_comparisons'].append(mode_comparison)
            
            # 修正分析
            revision_analysis = self.analyze_revision_impact(event_tag)
            report['summary']['revision_analyses'].append(revision_analysis)
        
        # 全体統計
        all_event_analysis = self.analyze_event_diversity(None)
        all_mode_comparison = self.compare_solo_vs_social(None)
        all_revision_analysis = self.analyze_revision_impact(None)
        
        report['overall'] = {
            'diversity': all_event_analysis,
            'mode_comparison': all_mode_comparison,
            'revision_impact': all_revision_analysis
        }
        
        return report

def main():
    """メイン実行関数"""
    print("=" * 60)
    print("ことイミ日記 - 研究者向け分析ツール")
    print("=" * 60)
    
    analyzer = MeaningDiversityAnalyzer()
    
    try:
        # サンプル分析実行
        print("\n1. 出来事「work_late」の多様性分析")
        work_late_analysis = analyzer.analyze_event_diversity('work_late')
        print(json.dumps(work_late_analysis, ensure_ascii=False, indent=2))
        
        print("\n2. Solo vs Social モード比較")
        mode_comparison = analyzer.compare_solo_vs_social()
        print(json.dumps(mode_comparison, ensure_ascii=False, indent=2))
        
        print("\n3. 他者結果表示後の変化分析")
        revision_analysis = analyzer.analyze_revision_impact()
        print(json.dumps(revision_analysis, ensure_ascii=False, indent=2))
        
        print("\n✅ 分析完了")
        
    except Exception as e:
        print(f"❌ 分析エラー: {e}")

if __name__ == '__main__':
    import datetime
    main()