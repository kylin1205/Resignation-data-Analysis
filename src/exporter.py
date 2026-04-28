"""
导出模块 - Excel和PDF报告导出
"""

import pandas as pd
from io import BytesIO
from typing import Dict, Optional
import streamlit as st
from datetime import datetime


class Exporter:
    """数据导出器"""

    def __init__(self):
        pass

    def export_to_excel(self,
                       monthly_stats: pd.DataFrame,
                       dept_stats: pd.DataFrame,
                       departures_df: pd.DataFrame,
                       month_key: str) -> BytesIO:
        """
        导出分析数据为Excel

        Args:
            monthly_stats: 月度统计
            dept_stats: 部门统计
            departures_df: 离职明细
            month_key: 月份

        Returns:
            BytesIO: Excel文件流
        """
        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet1: 封面信息
            cover_data = {
                '报表名称': ['员工离职分析报告'],
                '分析月份': [month_key.replace('-', '年') + '月'],
                '生成时间': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            }
            pd.DataFrame(cover_data).to_excel(writer, sheet_name='报告摘要', index=False)

            # Sheet2: 月度汇总
            if not monthly_stats.empty:
                monthly_export = monthly_stats.copy()
                monthly_export.columns = ['月份', '期初人数', '期末人数', '平均人数', '离职人数', '离职率(%)']
                monthly_export.to_excel(writer, sheet_name='月度汇总', index=False)

            # Sheet3: 部门统计
            if not dept_stats.empty:
                dept_export = dept_stats.copy()
                dept_export = dept_export.sort_values('departure_count', ascending=False)
                dept_export.columns = ['部门', '期初人数', '期末人数', '平均人数', '离职人数', '离职率(%)']
                dept_export.to_excel(writer, sheet_name='部门统计', index=False)

            # Sheet4: 离职明细
            if not departures_df.empty:
                departure_export = departures_df.copy()
                # 选择展示列
                display_cols = ['employee_id', 'department_1', 'department_2',
                               'level', 'leave_type', 'leave_reason', 'tenure_years']
                display_cols = [c for c in display_cols if c in departure_export.columns]

                departure_export = departure_export[display_cols].copy()
                departure_export.columns = ['工号', '一级部门', '二级部门', '职级', '离职类型', '离职原因', '司龄(年)']
                departure_export.to_excel(writer, sheet_name='离职明细', index=False)

            # Sheet5: 离职类型分布
            if not departures_df.empty and 'leave_type' in departures_df.columns:
                leave_type_dist = departures_df['leave_type'].value_counts().reset_index()
                leave_type_dist.columns = ['离职类型', '人数']
                leave_type_dist['占比(%)'] = (leave_type_dist['人数'] / leave_type_dist['人数'].sum() * 100).round(2)
                leave_type_dist.to_excel(writer, sheet_name='离职类型', index=False)

            # Sheet6: 离职原因分布
            if not departures_df.empty and 'leave_reason' in departures_df.columns:
                leave_reason_dist = departures_df['leave_reason'].value_counts().reset_index()
                leave_reason_dist.columns = ['离职原因', '人数']
                leave_reason_dist['占比(%)'] = (leave_reason_dist['人数'] / leave_reason_dist['人数'].sum() * 100).round(2)
                leave_reason_dist.to_excel(writer, sheet_name='离职原因', index=False)

        output.seek(0)
        return output

    def generate_excel_filename(self, month_key: str) -> str:
        """
        生成Excel文件名

        Args:
            month_key: 月份

        Returns:
            str: 文件名
        """
        return f"离职分析报告_{month_key}.xlsx"

    def export_to_pdf(self,
                      monthly_stats: pd.DataFrame,
                      dept_stats: pd.DataFrame,
                      departures_df: pd.DataFrame,
                      month_key: str,
                      ai_analysis: str = None) -> BytesIO:
        """
        导出PDF分析报告

        Args:
            monthly_stats: 月度统计
            dept_stats: 部门统计
            departures_df: 离职明细
            month_key: 月份
            ai_analysis: AI分析报告（可选）

        Returns:
            BytesIO: PDF文件流
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.units import cm
        except ImportError:
            st.error("请安装reportlab库: pip install reportlab")
            return BytesIO()

        output = BytesIO()

        # 创建PDF文档
        doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        # 样式
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # 居中
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#4F46E5')
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )

        elements = []

        # 标题
        elements.append(Paragraph("员工离职分析报告", title_style))
        elements.append(Paragraph(f"分析月份：{month_key.replace('-', '年')}月", body_style))
        elements.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
        elements.append(Spacer(1, 20))

        # 整体数据
        current_month = monthly_stats[monthly_stats['month_key'] == month_key]
        if not current_month.empty:
            row = current_month.iloc[0]
            elements.append(Paragraph("一、整体数据概况", heading_style))

            summary_data = [
                ['指标', '数值'],
                ['平均人数', f"{int(row['avg_count'])}人"],
                ['离职人数', f"{int(row['departure_count'])}人"],
                ['离职率', f"{row['attrition_rate']:.2f}%"]
            ]

            summary_table = Table(summary_data, colWidths=[5*cm, 5*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 20))

        # 部门统计
        if not dept_stats.empty:
            elements.append(Paragraph("二、各部门离职情况", heading_style))

            dept_data = [['部门', '离职人数', '离职率']]
            for _, dept in dept_stats.sort_values('departure_count', ascending=False).head(10).iterrows():
                dept_data.append([
                    dept['department'],
                    f"{int(dept['departure_count'])}人",
                    f"{dept['attrition_rate']:.2f}%"
                ])

            dept_table = Table(dept_data, colWidths=[7*cm, 3*cm, 3*cm])
            dept_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(dept_table)
            elements.append(Spacer(1, 20))

        # 离职类型分析
        if not departures_df.empty and 'leave_type' in departures_df.columns:
            elements.append(Paragraph("三、离职类型分析", heading_style))

            type_counts = departures_df['leave_type'].value_counts()
            total = len(departures_df)

            type_data = [['离职类型', '人数', '占比']]
            for leave_type, count in type_counts.items():
                type_data.append([
                    leave_type,
                    f"{int(count)}人",
                    f"{count/total*100:.1f}%"
                ])

            type_table = Table(type_data, colWidths=[5*cm, 3*cm, 3*cm])
            type_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(type_table)
            elements.append(Spacer(1, 20))

        # AI分析报告
        if ai_analysis:
            elements.append(Paragraph("四、AI智能分析", heading_style))
            # 简单处理AI报告，移除markdown格式
            lines = ai_analysis.replace('#', '').replace('*', '').split('\n')
            for line in lines:
                if line.strip():
                    elements.append(Paragraph(line.strip(), body_style))

        # 页脚
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("— 员工离职数据分析系统 —", ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1,
            textColor=colors.gray
        )))

        # 构建PDF
        doc.build(elements)
        output.seek(0)

        return output

    def generate_pdf_filename(self, month_key: str) -> str:
        """
        生成PDF文件名

        Args:
            month_key: 月份

        Returns:
            str: 文件名
        """
        return f"离职分析报告_{month_key}.pdf"
