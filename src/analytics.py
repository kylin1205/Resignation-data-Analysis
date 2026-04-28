"""
分析计算模块 - 离职率、趋势、指标计算
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class Analytics:
    """离职数据分析引擎"""

    def __init__(self):
        pass

    def calculate_monthly_attrition_rate(self, start_count: int, end_count: int,
                                        departure_count: int) -> Dict:
        """
        计算月度离职率

        Args:
            start_count: 期初人数
            end_count: 期末人数
            departure_count: 离职人数

        Returns:
            Dict: 包含各项指标的计算结果
        """
        avg_count = (start_count + end_count) / 2
        attrition_rate = (departure_count / avg_count * 100) if avg_count > 0 else 0

        return {
            'start_count': start_count,
            'end_count': end_count,
            'avg_count': round(avg_count, 1),
            'departure_count': departure_count,
            'attrition_rate': round(attrition_rate, 2),
            'retention_rate': round(100 - attrition_rate, 2)
        }

    def calculate_cumulative_attrition(self, monthly_stats: pd.DataFrame) -> Dict:
        """
        计算累计离职率

        Args:
            monthly_stats: 月度统计数据DataFrame

        Returns:
            Dict: 累计离职指标
        """
        if monthly_stats.empty:
            return {
                'total_departures': 0,
                'cumulative_avg': 0,
                'cumulative_rate': 0
            }

        total_departures = monthly_stats['departure_count'].sum()
        cumulative_avg = monthly_stats['avg_count'].mean()
        cumulative_rate = (total_departures / cumulative_avg * 100) if cumulative_avg > 0 else 0

        return {
            'total_departures': total_departures,
            'cumulative_avg': round(cumulative_avg, 1),
            'cumulative_rate': round(cumulative_rate, 2)
        }

    def analyze_department_attrition(self, dept_stats: pd.DataFrame,
                                   overall_rate: float) -> pd.DataFrame:
        """
        分析各部门离职情况与整体对比

        Args:
            dept_stats: 部门统计数据
            overall_rate: 整体离职率

        Returns:
            pd.DataFrame: 带分析结果的部门数据
        """
        if dept_stats.empty:
            return pd.DataFrame()

        df = dept_stats.copy()

        # 计算与整体离职率的差异
        df['rate_diff'] = df['attrition_rate'] - overall_rate

        # 标记异常值
        df['risk_level'] = df['rate_diff'].apply(lambda x: '高风险' if x > 1.5 else
                                                  ('中风险' if x > 0.5 else '正常'))

        # 排序
        df = df.sort_values('attrition_rate', ascending=False)

        return df

    def analyze_tenure_pattern(self, departures_df: pd.DataFrame) -> Dict:
        """
        分析司龄分布模式

        Args:
            departures_df: 离职数据

        Returns:
            Dict: 司龄分析结果
        """
        if departures_df.empty or 'tenure_years' not in departures_df.columns:
            return {}

        tenure = departures_df['tenure_years'].dropna()

        if tenure.empty:
            return {}

        # 基础统计
        stats = {
            'avg_tenure': round(tenure.mean(), 2),
            'median_tenure': round(tenure.median(), 2),
            'min_tenure': round(tenure.min(), 2),
            'max_tenure': round(tenure.max(), 2),
            'total_count': len(tenure)
        }

        # 各区间人数
        categories = ['0-0.5年', '0.5-1年', '1-3年', '3-5年', '5年以上']
        for cat in categories:
            if 'tenure_category' in departures_df.columns:
                count = len(departures_df[departures_df['tenure_category'] == cat])
                stats[f'count_{cat}'] = count
                stats[f'pct_{cat}'] = round(count / len(tenure) * 100, 1) if len(tenure) > 0 else 0

        return stats

    def analyze_leave_type_ratio(self, departures_df: pd.DataFrame) -> Dict:
        """
        分析离职类型占比

        Args:
            departures_df: 离职数据

        Returns:
            Dict: 离职类型分析结果
        """
        if departures_df.empty or 'leave_type' not in departures_df.columns:
            return {}

        type_counts = departures_df['leave_type'].value_counts()
        total = len(departures_df)

        result = {
            'total': total,
            'types': {}
        }

        for leave_type, count in type_counts.items():
            result['types'][leave_type] = {
                'count': int(count),
                'percentage': round(count / total * 100, 1)
            }

        # 计算主动/被动离职比例
        voluntary = type_counts.get('主动离职', 0)
        involuntary = type_counts.get('被动离职', 0)

        result['voluntary_count'] = int(voluntary)
        result['involuntary_count'] = int(involuntary)
        result['voluntary_pct'] = round(voluntary / total * 100, 1) if total > 0 else 0
        result['involuntary_pct'] = round(involuntary / total * 100, 1) if total > 0 else 0

        return result

    def get_trend_data(self, monthly_stats: pd.DataFrame) -> Dict:
        """
        获取趋势数据

        Args:
            monthly_stats: 月度统计数据

        Returns:
            Dict: 趋势数据
        """
        if monthly_stats.empty:
            return {}

        # 按月份排序
        df = monthly_stats.sort_values('month_key')

        return {
            'months': df['month_key'].tolist(),
            'attrition_rates': df['attrition_rate'].tolist(),
            'departure_counts': df['departure_count'].tolist(),
            'avg_counts': df['avg_count'].tolist()
        }

    def calculate_risk_score(self, dept_stats: pd.DataFrame,
                           departures_df: pd.DataFrame,
                           overall_rate: float) -> pd.DataFrame:
        """
        计算部门风险评分

        Args:
            dept_stats: 部门统计
            departures_df: 离职明细
            overall_rate: 整体离职率

        Returns:
            pd.DataFrame: 带风险评分的部门数据
        """
        if dept_stats.empty:
            return pd.DataFrame()

        df = dept_stats.copy()

        # 基础风险分数（基于离职率）
        df['base_risk'] = df['attrition_rate'].apply(
            lambda x: 100 if x > overall_rate * 2 else
                      (70 if x > overall_rate * 1.5 else
                       (40 if x > overall_rate else 10))
        )

        # 中坚力量流失风险
        if 'tenure_category' in departures_df.columns:
            middle_strength = departures_df[
                (departures_df['department_1'].isin(df['department'])) &
                (departures_df['tenure_category'] == '1-3年')
            ].groupby('department_1').size()

            df = df.merge(
                middle_strength.reset_index().rename(columns={
                    'department_1': 'department',
                    0: 'middle_strength_loss'
                }),
                on='department',
                how='left'
            )
            df['middle_strength_loss'] = df['middle_strength_loss'].fillna(0)

            # 调整风险分数
            df['base_risk'] = df.apply(
                lambda row: min(100, row['base_risk'] + row['middle_strength_loss'] * 5)
                if row['middle_strength_loss'] > 2 else row['base_risk'],
                axis=1
            )

        # 风险等级
        df['risk_score'] = df['base_risk']
        df['risk_level'] = df['risk_score'].apply(
            lambda x: '高风险' if x >= 70 else
                      ('中风险' if x >= 40 else '低风险')
        )

        return df.sort_values('risk_score', ascending=False)

    def generate_summary_insights(self, monthly_stats: pd.DataFrame,
                                 dept_stats: pd.DataFrame,
                                 departures_df: pd.DataFrame,
                                 month_key: str) -> Dict:
        """
        生成汇总洞察

        Args:
            monthly_stats: 月度统计
            dept_stats: 部门统计
            departures_df: 离职明细
            month_key: 当前月份

        Returns:
            Dict: 洞察数据
        """
        insights = {
            'period': month_key,
            'summary': {},
            'warnings': [],
            'highlights': []
        }

        # 获取当前月数据
        current = monthly_stats[monthly_stats['month_key'] == month_key]
        if current.empty:
            return insights

        row = current.iloc[0]
        insights['summary'] = {
            'avg_count': int(row['avg_count']),
            'departures': int(row['departure_count']),
            'attrition_rate': row['attrition_rate']
        }

        # 计算趋势
        if len(monthly_stats) > 1:
            prev = monthly_stats[monthly_stats['month_key'] < month_key].iloc[-1]
            rate_change = row['attrition_rate'] - prev['attrition_rate']
            insights['summary']['rate_change'] = round(rate_change, 2)
            insights['summary']['trend'] = '上升' if rate_change > 0 else '下降'

        # 高风险部门
        if not dept_stats.empty:
            high_risk = dept_stats[dept_stats['risk_level'] == '高风险']
            for _, dept in high_risk.iterrows():
                insights['warnings'].append({
                    'type': '部门风险',
                    'department': dept['department'],
                    'attrition_rate': dept['attrition_rate'],
                    'departures': int(dept['departure_count'])
                })

        # 关键发现
        if not departures_df.empty:
            # 新人流失
            newbies = departures_df[
                (departures_df['month_key'] == month_key) &
                (departures_df['tenure_years'] <= 0.5)
            ]
            if len(newbies) > 0:
                insights['warnings'].append({
                    'type': '新人流失',
                    'count': len(newbies),
                    'message': f'本月有{len(newbies)}名司龄不足半年的新人离职'
                })

        return insights
