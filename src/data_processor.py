"""
数据处理模块 - 数据清洗、转换和标准化
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re


class DataProcessor:
    """数据处理器"""

    def __init__(self):
        # 司龄区间定义
        self.tenure_ranges = [
            {"name": "新人", "min": 0, "max": 0.5, "label": "0-0.5年"},
            {"name": "初级", "min": 0.5, "max": 1, "label": "0.5-1年"},
            {"name": "中坚", "min": 1, "max": 3, "label": "1-3年"},
            {"name": "资深", "min": 3, "max": 5, "label": "3-5年"},
            {"name": "专家", "min": 5, "max": 100, "label": "5年以上"}
        ]

        # 离职类型标准化
        self.leave_type_mapping = {
            '主动离职': ['主动离职', '主动', '自己辞职', '个人辞职', '辞职'],
            '被动离职': ['被动离职', '被动', '公司辞退', '辞退', '裁员', '合同到期不续签', '试用期不胜任', '绩效不达标']
        }

    def clean_employee_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗员工数据

        Args:
            df: 原始员工数据

        Returns:
            pd.DataFrame: 清洗后的数据
        """
        df = df.copy()

        # 去除完全重复的行
        df = df.drop_duplicates()

        # 工号去重处理：保留最新记录
        if 'employee_id' in df.columns:
            df = df.sort_values('month_key', ascending=False)
            df = df.drop_duplicates(subset=['employee_id'], keep='first')

        # 填充缺失值
        if 'department_1' in df.columns:
            df['department_1'] = df['department_1'].fillna('未知部门')

        if 'status' in df.columns:
            df['status'] = df['status'].fillna('在职')

        # 数据类型转换
        if 'join_date' in df.columns:
            df['join_date'] = pd.to_datetime(df['join_date'], errors='coerce')

        if 'tenure_years' in df.columns:
            df['tenure_years'] = pd.to_numeric(df['tenure_years'], errors='coerce')

        return df

    def clean_departure_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗离职数据

        Args:
            df: 原始离职数据

        Returns:
            pd.DataFrame: 清洗后的数据
        """
        df = df.copy()

        # 去除完全重复的行
        df = df.drop_duplicates()

        # 标准化离职类型
        if 'leave_type' in df.columns:
            df['leave_type'] = df['leave_type'].apply(self._normalize_leave_type)

        # 标准化离职原因
        if 'leave_reason' in df.columns:
            df['leave_reason'] = df['leave_reason'].fillna('未知原因')

        # 数据类型转换
        if 'leave_date' in df.columns:
            df['leave_date'] = pd.to_datetime(df['leave_date'], errors='coerce')

        if 'join_date' in df.columns:
            df['join_date'] = pd.to_datetime(df['join_date'], errors='coerce')

        if 'tenure_years' in df.columns:
            df['tenure_years'] = pd.to_numeric(df['tenure_years'], errors='coerce')

        # 填充缺失值
        if 'department_1' in df.columns:
            df['department_1'] = df['department_1'].fillna('未知部门')

        if 'level' in df.columns:
            df['level'] = df['level'].fillna('未知职级')

        return df

    def _normalize_leave_type(self, leave_type: str) -> str:
        """
        标准化离职类型

        Args:
            leave_type: 原始离职类型

        Returns:
            str: 标准化后的离职类型
        """
        if pd.isna(leave_type):
            return '未知'

        leave_type = str(leave_type).strip()

        for standard_type, variants in self.leave_type_mapping.items():
            for variant in variants:
                if variant in leave_type:
                    return standard_type

        return leave_type

    def calculate_tenure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算司龄（如果原始数据没有）

        Args:
            df: 员工/离职数据

        Returns:
            pd.DataFrame: 包含司龄的数据
        """
        df = df.copy()

        if 'tenure_years' not in df.columns or df['tenure_years'].isna().all():
            if 'join_date' in df.columns and 'leave_date' in df.columns:
                # 计算司龄（年）
                df['tenure_years'] = (df['leave_date'] - df['join_date']).dt.days / 365.25
            elif 'join_date' in df.columns:
                # 以当前日期计算
                df['tenure_years'] = (datetime.now() - df['join_date']).dt.days / 365.25

        return df

    def categorize_tenure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为司龄分配区间类别

        Args:
            df: 包含司龄的数据

        Returns:
            pd.DataFrame: 包含司龄区间的数据
        """
        df = df.copy()

        if 'tenure_years' not in df.columns:
            df['tenure_category'] = '未知'
            return df

        def get_tenure_category(tenure):
            if pd.isna(tenure):
                return '未知'
            for range_info in self.tenure_ranges:
                if range_info['min'] <= tenure < range_info['max']:
                    return range_info['label']
            if tenure >= 5:
                return '5年以上'
            return '未知'

        df['tenure_category'] = df['tenure_years'].apply(get_tenure_category)

        return df

    def aggregate_by_department(self, employees_df: pd.DataFrame,
                                departures_df: pd.DataFrame,
                                month_key: str) -> pd.DataFrame:
        """
        按部门聚合数据

        Args:
            employees_df: 员工数据
            departures_df: 离职数据
            month_key: 月份

        Returns:
            pd.DataFrame: 部门统计数据
        """
        # 期初人数（当月在职）
        start_count = len(employees_df[employees_df['month_key'] == month_key])

        # 期末人数（下月期初）
        months = sorted(employees_df['month_key'].unique())
        month_idx = months.index(month_key) if month_key in months else -1
        if month_idx < len(months) - 1:
            next_month = months[month_idx + 1]
            end_count = len(employees_df[employees_df['month_key'] == next_month])
        else:
            end_count = start_count  # 如果是最后一个月，期末=期初

        # 离职人数
        departures = departures_df[departures_df['month_key'] == month_key]
        departure_count = len(departures)

        # 计算平均人数和离职率
        avg_count = (start_count + end_count) / 2
        attrition_rate = (departure_count / avg_count * 100) if avg_count > 0 else 0

        return pd.DataFrame([{
            'month_key': month_key,
            'start_count': start_count,
            'end_count': end_count,
            'avg_count': avg_count,
            'departure_count': departure_count,
            'attrition_rate': attrition_rate
        }])

    def aggregate_department_stats(self, employees_df: pd.DataFrame,
                                   departures_df: pd.DataFrame,
                                   month_key: str) -> pd.DataFrame:
        """
        按一级部门聚合统计数据

        Args:
            employees_df: 员工数据
            departures_df: 离职数据
            month_key: 月份

        Returns:
            pd.DataFrame: 各部门统计数据
        """
        stats = []

        # 获取所有一级部门
        all_depts = set(employees_df['department_1'].unique()) | \
                    set(departures_df['department_1'].unique())

        for dept in all_depts:
            if pd.isna(dept):
                continue

            # 当月在职人数
            start = len(employees_df[(employees_df['month_key'] == month_key) &
                                     (employees_df['department_1'] == dept)])

            # 下月在職人數
            months = sorted(employees_df['month_key'].unique())
            month_idx = months.index(month_key) if month_key in months else -1
            if month_idx < len(months) - 1:
                next_month = months[month_idx + 1]
                end = len(employees_df[(employees_df['month_key'] == next_month) &
                                       (employees_df['department_1'] == dept)])
            else:
                end = start

            # 离职人数
            departure_count = len(departures_df[(departures_df['month_key'] == month_key) &
                                                (departures_df['department_1'] == dept)])

            # 计算
            avg = (start + end) / 2
            rate = (departure_count / avg * 100) if avg > 0 else 0

            stats.append({
                'department': dept,
                'start_count': start,
                'end_count': end,
                'avg_count': avg,
                'departure_count': departure_count,
                'attrition_rate': rate
            })

        df = pd.DataFrame(stats)
        if not df.empty:
            df = df.sort_values('departure_count', ascending=False)

        return df

    def prepare_monthly_summary(self, employees_df: pd.DataFrame,
                                departures_df: pd.DataFrame) -> pd.DataFrame:
        """
        准备月度汇总数据

        Args:
            employees_df: 员工数据
            departures_df: 离职数据

        Returns:
            pd.DataFrame: 月度汇总数据
        """
        summary = []

        months = sorted(employees_df['month_key'].unique())

        for i, month in enumerate(months):
            # 期初人数：使用role='期初'的记录
            if 'role' in employees_df.columns:
                start_count = len(employees_df[
                    (employees_df['month_key'] == month) &
                    (employees_df['role'] == '期初')
                ])
            else:
                start_count = len(employees_df[employees_df['month_key'] == month])

            # 期末人数：使用role='期末'的记录，如果没有则使用下月role='期初'
            if 'role' in employees_df.columns:
                end_df = employees_df[
                    (employees_df['month_key'] == month) &
                    (employees_df['role'] == '期末')
                ]
                if len(end_df) == 0 and i < len(months) - 1:
                    next_month = months[i + 1]
                    end_count = len(employees_df[
                        (employees_df['month_key'] == next_month) &
                        (employees_df['role'] == '期初')
                    ])
                else:
                    end_count = len(end_df)
            else:
                end_count = start_count

            # 离职人数
            departure_count = len(departures_df[departures_df['month_key'] == month])

            # 计算
            avg_count = (start_count + end_count) / 2
            attrition_rate = (departure_count / avg_count * 100) if avg_count > 0 else 0

            summary.append({
                'month_key': month,
                'start_count': int(start_count),
                'end_count': int(end_count),
                'avg_count': round(avg_count, 1),
                'departure_count': int(departure_count),
                'attrition_rate': round(attrition_rate, 2)
            })

        return pd.DataFrame(summary)

    def get_departure_distribution(self, departures_df: pd.DataFrame,
                                    month_key: str,
                                    group_by: str) -> pd.DataFrame:
        """
        获取离职分布数据

        Args:
            departures_df: 离职数据
            month_key: 月份
            group_by: 分组字段

        Returns:
            pd.DataFrame: 分布数据
        """
        departures = departures_df[departures_df['month_key'] == month_key].copy()

        if departures.empty:
            return pd.DataFrame({'category': [], 'count': [], 'percentage': []})

        # 分组统计
        dist = departures.groupby(group_by).size().reset_index(name='count')

        # 计算百分比
        dist['percentage'] = (dist['count'] / dist['count'].sum() * 100).round(2)

        # 按数量降序排列
        dist = dist.sort_values('count', ascending=False)

        # 重命名列
        dist.columns = ['category', 'count', 'percentage']

        return dist

    def get_departure_details(self, departures_df: pd.DataFrame,
                             month_key: str) -> pd.DataFrame:
        """
        获取离职人员明细

        Args:
            departures_df: 离职数据
            month_key: 月份

        Returns:
            pd.DataFrame: 离职人员明细
        """
        departures = departures_df[departures_df['month_key'] == month_key].copy()

        if departures.empty:
            return pd.DataFrame()

        # 选择展示列
        display_columns = [
            'employee_id', 'department_1', 'department_2', 'position',
            'level', 'leave_type', 'leave_reason', 'tenure_years', 'leave_date'
        ]

        # 只保留存在的列
        display_columns = [col for col in display_columns if col in departures.columns]

        result = departures[display_columns].copy()

        # 重命名列为中文
        column_names = {
            'employee_id': '工号',
            'department_1': '一级部门',
            'department_2': '二级部门',
            'position': '职务',
            'level': '职级',
            'leave_type': '离职类型',
            'leave_reason': '离职原因',
            'tenure_years': '司龄(年)',
            'leave_date': '离职日期'
        }

        result = result.rename(columns=column_names)

        # 格式化
        if '司龄(年)' in result.columns:
            result['司龄(年)'] = result['司龄(年)'].round(2)

        if '离职日期' in result.columns:
            result['离职日期'] = pd.to_datetime(result['离职日期']).dt.strftime('%Y-%m-%d')

        return result.sort_values('离职日期', ascending=False)
