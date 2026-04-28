"""
数据库模块 - SQLite数据持久化
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os


class Database:
    """SQLite数据库管理器"""

    def __init__(self, db_path: str = "data/attrition.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()

    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 人员表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                name TEXT,
                gender TEXT,
                department_1 TEXT,
                department_2 TEXT,
                department_3 TEXT,
                department_4 TEXT,
                department TEXT,
                position TEXT,
                level TEXT,
                join_date TEXT,
                org_full_name TEXT,
                status TEXT,
                email TEXT,
                work_location TEXT,
                code TEXT,
                employment_type TEXT,
                employment_form TEXT,
                identity_category TEXT,
                company TEXT,
                direct_leader TEXT,
                direct_leader_id TEXT,
                dept_leader TEXT,
                dept_leader_email TEXT,
                hrbp TEXT,
                hrbp_email TEXT,
                source TEXT,
                birth_date TEXT,
                age INTEGER,
                tenure_years REAL,
                education TEXT,
                graduated_school TEXT,
                major TEXT,
                month_key TEXT NOT NULL,
                sheet_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(employee_id, month_key)
            )
        ''')

        # 离职记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departure_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                department_1 TEXT,
                department_2 TEXT,
                department_3 TEXT,
                department_4 TEXT,
                position TEXT,
                join_date TEXT,
                leave_date TEXT,
                leave_type TEXT,
                leave_reason TEXT,
                leave_reason_detail TEXT,
                bp_leave_reason TEXT,
                status TEXT,
                level TEXT,
                tenure_years REAL,
                tenure_category TEXT,
                month_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(employee_id, month_key)
            )
        ''')

        # 月度统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_key TEXT UNIQUE NOT NULL,
                start_count INTEGER,
                end_count INTEGER,
                avg_count REAL,
                departure_count INTEGER,
                attrition_rate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 部门统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS department_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_key TEXT NOT NULL,
                department TEXT NOT NULL,
                start_count INTEGER,
                end_count INTEGER,
                avg_count REAL,
                departure_count INTEGER,
                attrition_rate REAL,
                risk_level TEXT,
                risk_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(month_key, department)
            )
        ''')

        conn.commit()
        conn.close()

    def save_employees(self, df: pd.DataFrame) -> int:
        """
        保存员工数据

        Args:
            df: 员工数据DataFrame

        Returns:
            int: 保存的记录数
        """
        if df.empty:
            return 0

        conn = self._get_connection()
        count = 0

        try:
            for _, row in df.iterrows():
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO employees (
                        employee_id, name, gender, department_1, department_2,
                        department_3, department_4, department, position, level,
                        join_date, org_full_name, status, email, work_location,
                        code, employment_type, employment_form, identity_category,
                        company, direct_leader, direct_leader_id, dept_leader,
                        dept_leader_email, hrbp, hrbp_email, source, birth_date,
                        age, tenure_years, month_key, sheet_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('employee_id'), row.get('name'), row.get('gender'),
                    row.get('department_1'), row.get('department_2'),
                    row.get('department_3'), row.get('department_4'), row.get('department'),
                    row.get('position'), row.get('level'), row.get('join_date'),
                    row.get('org_full_name'), row.get('status'), row.get('email'),
                    row.get('work_location'), row.get('code'), row.get('employment_type'),
                    row.get('employment_form'), row.get('identity_category'),
                    row.get('company'), row.get('direct_leader'), row.get('direct_leader_id'),
                    row.get('dept_leader'), row.get('dept_leader_email'),
                    row.get('hrbp'), row.get('hrbp_email'), row.get('source'),
                    row.get('birth_date'), row.get('age'), row.get('tenure_years'),
                    row.get('month_key'), row.get('sheet_type')
                ))
                count += 1

            conn.commit()
        finally:
            conn.close()

        return count

    def save_departures(self, df: pd.DataFrame) -> int:
        """
        保存离职记录

        Args:
            df: 离职记录DataFrame

        Returns:
            int: 保存的记录数
        """
        if df.empty:
            return 0

        conn = self._get_connection()
        count = 0

        try:
            for _, row in df.iterrows():
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO departure_records (
                        employee_id, department_1, department_2, department_3,
                        department_4, position, join_date, leave_date, leave_type,
                        leave_reason, leave_reason_detail, bp_leave_reason,
                        status, level, tenure_years, tenure_category, month_key
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('employee_id'), row.get('department_1'), row.get('department_2'),
                    row.get('department_3'), row.get('department_4'), row.get('position'),
                    row.get('join_date'), row.get('leave_date'), row.get('leave_type'),
                    row.get('leave_reason'), row.get('leave_reason_detail'),
                    row.get('bp_leave_reason'), row.get('status'), row.get('level'),
                    row.get('tenure_years'), row.get('tenure_category'), row.get('month_key')
                ))
                count += 1

            conn.commit()
        finally:
            conn.close()

        return count

    def save_monthly_stats(self, df: pd.DataFrame) -> int:
        """
        保存月度统计

        Args:
            df: 月度统计数据DataFrame

        Returns:
            int: 保存的记录数
        """
        if df.empty:
            return 0

        conn = self._get_connection()
        count = 0

        try:
            for _, row in df.iterrows():
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO monthly_stats (
                        month_key, start_count, end_count, avg_count,
                        departure_count, attrition_rate
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    row['month_key'], row['start_count'], row['end_count'],
                    row['avg_count'], row['departure_count'], row['attrition_rate']
                ))
                count += 1

            conn.commit()
        finally:
            conn.close()

        return count

    def save_department_stats(self, df: pd.DataFrame, month_key: str) -> int:
        """
        保存部门统计

        Args:
            df: 部门统计数据DataFrame
            month_key: 月份

        Returns:
            int: 保存的记录数
        """
        if df.empty:
            return 0

        conn = self._get_connection()
        count = 0

        try:
            for _, row in df.iterrows():
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO department_stats (
                        month_key, department, start_count, end_count,
                        avg_count, departure_count, attrition_rate,
                        risk_level, risk_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    month_key, row['department'], row.get('start_count', 0),
                    row.get('end_count', 0), row.get('avg_count', 0),
                    row.get('departure_count', 0), row.get('attrition_rate', 0),
                    row.get('risk_level', ''), row.get('risk_score', 0)
                ))
                count += 1

            conn.commit()
        finally:
            conn.close()

        return count

    def get_employees(self, month_key: str = None) -> pd.DataFrame:
        """
        获取员工数据

        Args:
            month_key: 月份筛选（可选）

        Returns:
            pd.DataFrame: 员工数据
        """
        conn = self._get_connection()

        try:
            if month_key:
                df = pd.read_sql_query(
                    'SELECT * FROM employees WHERE month_key = ?',
                    conn, params=(month_key,)
                )
            else:
                df = pd.read_sql_query('SELECT * FROM employees', conn)

            return df
        finally:
            conn.close()

    def get_departures(self, month_key: str = None) -> pd.DataFrame:
        """
        获取离职记录

        Args:
            month_key: 月份筛选（可选）

        Returns:
            pd.DataFrame: 离职记录
        """
        conn = self._get_connection()

        try:
            if month_key:
                df = pd.read_sql_query(
                    'SELECT * FROM departure_records WHERE month_key = ?',
                    conn, params=(month_key,)
                )
            else:
                df = pd.read_sql_query('SELECT * FROM departure_records', conn)

            return df
        finally:
            conn.close()

    def get_monthly_stats(self) -> pd.DataFrame:
        """
        获取月度统计

        Returns:
            pd.DataFrame: 月度统计数据
        """
        conn = self._get_connection()

        try:
            df = pd.read_sql_query(
                'SELECT * FROM monthly_stats ORDER BY month_key',
                conn
            )
            return df
        finally:
            conn.close()

    def get_department_stats(self, month_key: str = None) -> pd.DataFrame:
        """
        获取部门统计

        Args:
            month_key: 月份筛选（可选）

        Returns:
            pd.DataFrame: 部门统计数据
        """
        conn = self._get_connection()

        try:
            if month_key:
                df = pd.read_sql_query(
                    'SELECT * FROM department_stats WHERE month_key = ? ORDER BY attrition_rate DESC',
                    conn, params=(month_key,)
                )
            else:
                df = pd.read_sql_query(
                    'SELECT * FROM department_stats ORDER BY month_key, attrition_rate DESC',
                    conn
                )

            return df
        finally:
            conn.close()

    def clear_all_data(self):
        """清空所有数据"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM employees')
        cursor.execute('DELETE FROM departure_records')
        cursor.execute('DELETE FROM monthly_stats')
        cursor.execute('DELETE FROM department_stats')

        conn.commit()
        conn.close()

    def get_data_summary(self) -> Dict:
        """
        获取数据摘要

        Returns:
            Dict: 数据摘要信息
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            summary = {}

            # 员工数
            cursor.execute('SELECT COUNT(DISTINCT employee_id) FROM employees')
            summary['total_employees'] = cursor.fetchone()[0]

            # 月份数
            cursor.execute('SELECT COUNT(DISTINCT month_key) FROM employees')
            summary['total_months'] = cursor.fetchone()[0]

            # 离职记录数
            cursor.execute('SELECT COUNT(*) FROM departure_records')
            summary['total_departures'] = cursor.fetchone()[0]

            # 可用月份列表
            cursor.execute('SELECT DISTINCT month_key FROM employees ORDER BY month_key')
            summary['available_months'] = [row[0] for row in cursor.fetchall()]

            return summary
        finally:
            conn.close()
