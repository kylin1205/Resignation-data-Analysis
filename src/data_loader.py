"""
数据加载模块 - Excel文件解析与数据提取
"""

import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import streamlit as st


class DataLoader:
    """Excel数据加载器"""

    def __init__(self, default_year: str = "2026"):
        self.month_pattern = re.compile(r'(\d{4})[年\-]?(\d{1,2})月?')
        self.simple_month_pattern = re.compile(r'^(\d{1,2})月')
        self.default_year = default_year  # 默认年份，可根据文件名调整
        self.supported_formats = ['.xlsx', '.xls']

    def load_excel(self, uploaded_file) -> Dict[str, pd.DataFrame]:
        """
        加载Excel文件并解析所有Sheet

        Args:
            uploaded_file: Streamlit上传的文件对象

        Returns:
            Dict[str, pd.DataFrame]: Sheet名称到DataFrame的映射
        """
        try:
            # 读取所有Sheet
            excel_file = pd.ExcelFile(uploaded_file)
            sheets = {}

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                if not df.empty:
                    sheets[sheet_name] = df

            return sheets

        except Exception as e:
            raise Exception(f"加载Excel文件失败: {str(e)}")

    def detect_months(self, sheets: Dict[str, pd.DataFrame]) -> List[str]:
        """
        从Sheet名称中检测数据所属月份

        Args:
            sheets: Sheet名称到DataFrame的映射

        Returns:
            List[str]: 检测到的月份列表，格式为"YYYY-MM"
        """
        months = set()
        detected_year = self.default_year

        for sheet_name in sheets.keys():
            # 尝试匹配带年份的格式: 2026年01月, 2026-01月, 202601月
            match = self.month_pattern.search(sheet_name)
            if match:
                year, month = match.groups()
                detected_year = year  # 更新检测到的年份
                month_str = f"{year}-{int(month):02d}"
                months.add(month_str)
            else:
                # 尝试匹配简单格式: 1月, 01月
                simple_match = self.simple_month_pattern.search(sheet_name)
                if simple_match:
                    month = simple_match.group(1)
                    month_str = f"{detected_year}-{int(month):02d}"
                    months.add(month_str)

        # 更新默认年份为检测到的年份
        if detected_year != self.default_year:
            self.default_year = detected_year

        return sorted(list(months))

    def get_sheet_month_mapping(self, sheet_name: str) -> Dict[str, str]:
        """
        根据Sheet名称判断其代表的月份关系

        Args:
            sheet_name: Sheet名称

        Returns:
            Dict: {'期初': 'YYYY-MM', '期末': 'YYYY-MM'} 或 {'离职': 'YYYY-MM'}
        """
        import re

        # 期初人数Sheet: "X月期初人数"、"X月期初数据"
        qichu_pattern = re.compile(r'(\d{1,2})月(期初数据|期初人数)')
        # 期末人数Sheet: "X月期末数据"、"X月期末人数"
        qimo_pattern = re.compile(r'(\d{1,2})月(?:期末数据|期末人数)')

        # 尝试匹配期初
        qichu_match = qichu_pattern.search(sheet_name)
        if qichu_match:
            month = int(qichu_match.group(1))
            result = {'期初': f"{self.default_year}-{month:02d}"}

            # 检查是否同时包含期末信息
            qimo_in_paren = re.search(r'（(\d{1,2})月期末', sheet_name)
            if qimo_in_paren:
                prev_month = int(qimo_in_paren.group(1))
                result['期末'] = f"{self.default_year}-{prev_month:02d}"

            return result

        # 尝试匹配期末
        qimo_match = qimo_pattern.search(sheet_name)
        if qimo_match:
            month = int(qimo_match.group(1))
            result = {'期末': f"{self.default_year}-{month:02d}"}

            # 检查是否同时包含下月期初信息
            qichu_in_paren = re.search(r'（(\d{1,2})月期初', sheet_name)
            if qichu_in_paren:
                next_month = int(qichu_in_paren.group(1))
                result['期初'] = f"{self.default_year}-{next_month:02d}"

            return result

        # 离职数据Sheet
        if '离职' in sheet_name:
            # 从Sheet内容中查找离职日期来确定月份
            return {'离职': 'unknown'}

        return {}

    def parse_sheet_type(self, sheet_name: str, df: pd.DataFrame) -> str:
        """
        根据Sheet名称和数据结构判断Sheet类型

        Args:
            sheet_name: Sheet名称
            df: 数据DataFrame

        Returns:
            str: "期初", "期末", "离职数据"
        """
        sheet_name_lower = sheet_name.lower()

        # 根据Sheet名称判断
        if '离职' in sheet_name:
            return "离职数据"
        elif '期初' in sheet_name:
            return "期初"
        elif '期末' in sheet_name:
            return "期末"

        # 根据数据结构判断
        columns_lower = [str(col).lower() for col in df.columns]

        # 离职数据通常有离职相关字段
        if any('离职' in col for col in df.columns):
            return "离职数据"

        # 期初/期末数据通常有人员状态字段
        if '人员状态' in df.columns:
            statuses = df['人员状态'].dropna().unique()
            if '在职' in statuses or len(df) > 100:
                # 期初数据通常人数较多
                if len(df) > 500:
                    return "期初"
                else:
                    return "期末"

        return "期初"  # 默认

    def extract_employees(self, df: pd.DataFrame, month_key: str, sheet_type: str) -> pd.DataFrame:
        """
        从Sheet中提取员工数据

        Args:
            df: 原始DataFrame
            month_key: 月份标识 (YYYY-MM)
            sheet_type: Sheet类型

        Returns:
            pd.DataFrame: 标准化后的员工数据
        """
        employees = pd.DataFrame()

        # 基础字段映射
        field_mapping = {
            '工号': 'employee_id',
            '姓名': 'name',
            '性别': 'gender',
            '一级组织': 'department_1',
            '二级组织': 'department_2',
            '三级组织': 'department_3',
            '四级组织': 'department_4',
            '部门': 'department',
            '职务': 'position',
            '职级': 'level',
            '入职日期': 'join_date',
            '组织全称': 'org_full_name',
            '人员状态': 'status',
            '电子邮件': 'email',
            '工作地点': 'work_location',
            '编码': 'code',
            '雇佣关系': 'employment_type',
            '用工形式': 'employment_form',
            '身份类别': 'identity_category',
            '公司': 'company',
            '直接上级': 'direct_leader',
            '直接上级工号': 'direct_leader_id',
            '部门负责人': 'dept_leader',
            '部门负责人邮箱': 'dept_leader_email',
            '分管领导': '分管领导',
            '分管领导邮箱': '分管领导邮箱',
            'HRBP': 'hrbp',
            'HRBP邮箱': 'hrbp_email',
            '人员来源': 'source',
            '出生日期': 'birth_date',
            '年龄': 'age',
            '累计司龄（年）': 'tenure_years',
            '最高学历': 'education',
            '毕业学校': 'graduated_school',
            '专业': 'major',
            '户籍所在地': 'hukou_location',
            '户口类别': 'hukou_type',
            '银行账号': 'bank_account',
            '银行': 'bank',
            '证件号码': 'id_number',
            '证件类型': 'id_type',
            '婚姻状况': 'marital_status',
            '政治面貌': 'political_status',
            '毕业时间': 'graduation_date',
            '专业导师': '专业导师',
            '专业导师工号': '专业导师工号',
            '管理导师': '管理导师',
            '管理导师工号': '管理导师工号',
            '试用期(月)': 'probation_months'
        }

        # 执行字段映射
        for orig_col, new_col in field_mapping.items():
            if orig_col in df.columns:
                employees[new_col] = df[orig_col]

        # 添加元数据
        employees['month_key'] = month_key
        employees['sheet_type'] = sheet_type

        return employees

    def extract_departures(self, df: pd.DataFrame, month_key: str) -> pd.DataFrame:
        """
        从离职数据Sheet中提取离职记录

        Args:
            df: 原始DataFrame
            month_key: 月份标识

        Returns:
            pd.DataFrame: 离职记录
        """
        departures = pd.DataFrame()

        # 离职数据字段映射
        field_mapping = {
            '工号': 'employee_id',
            '一级组织': 'department_1',
            '二级组织': 'department_2',
            '三级组织': 'department_3',
            '四级组织': 'department_4',
            '离职前职务': 'position',
            '入职日期': 'join_date',
            '最后工作日': 'leave_date',
            '离职类型': 'leave_type',
            '离职原因': 'leave_reason',
            '员工离职原因详细说明': 'leave_reason_detail',
            'BP输出离职原因': 'bp_leave_reason',
            '人员状态': 'status',
            '职级': 'level',
            '累计司龄（年）': 'tenure_years'
        }

        # 执行字段映射
        for orig_col, new_col in field_mapping.items():
            if orig_col in df.columns:
                departures[new_col] = df[orig_col]

        # 添加元数据
        departures['month_key'] = month_key

        return departures

    def get_column_info(self, df: pd.DataFrame) -> Dict:
        """
        获取DataFrame的列信息

        Args:
            df: DataFrame

        Returns:
            Dict: 列信息
        """
        return {
            'total_columns': len(df.columns),
            'total_rows': len(df),
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict()
        }

    def validate_data(self, sheets: Dict[str, pd.DataFrame]) -> Tuple[bool, List[str]]:
        """
        验证数据有效性

        Args:
            sheets: Sheet数据

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        if not sheets:
            errors.append("Excel文件为空或无法读取")
            return False, errors

        # 检查必需字段
        required_employee_fields = ['工号', '姓名']
        required_departure_fields = ['工号', '离职类型']

        for sheet_name, df in sheets.items():
            sheet_type = self.parse_sheet_type(sheet_name, df)

            if sheet_type == "离职数据":
                missing = [f for f in required_departure_fields if f not in df.columns]
                if missing:
                    errors.append(f"Sheet '{sheet_name}' 缺少必需字段: {', '.join(missing)}")
            else:
                missing = [f for f in required_employee_fields if f not in df.columns]
                if missing:
                    errors.append(f"Sheet '{sheet_name}' 缺少必需字段: {', '.join(missing)}")

        return len(errors) == 0, errors
