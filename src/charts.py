"""
图表生成模块 - 使用Plotly生成可视化图表
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Optional
import streamlit as st


class ChartGenerator:
    """图表生成器"""

    def __init__(self):
        # 配色方案
        self.colors = {
            'primary': '#4F46E5',      # 靛蓝色
            'secondary': '#10B981',    # 绿色
            'accent': '#F59E0B',       # 琥珀色
            'danger': '#EF4444',       # 红色
            'info': '#3B82F6',         # 蓝色
            'warning': '#F97316',     # 橙色
            'purple': '#8B5CF6',       # 紫色
            'pink': '#EC4899',         # 粉色
            'cyan': '#06B6D4',         # 青色
            'gray': '#6B7280'          # 灰色
        }

        # 饼图配色
        self.pie_colors = [
            self.colors['primary'],
            self.colors['secondary'],
            self.colors['accent'],
            self.colors['danger'],
            self.colors['info'],
            self.colors['purple'],
            self.colors['warning'],
            self.colors['pink']
        ]

    def create_department_combined_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        创建部门离职情况合并图表（纵向柱状图+折线图）
        过滤掉离职人数为0的部门

        Args:
            df: 部门统计数据

        Returns:
            go.Figure: Plotly图表对象
        """
        if df.empty:
            return self._empty_chart("暂无部门数据")

        # 过滤掉离职人数为0的部门
        df = df[df['departure_count'] > 0].copy()

        if df.empty:
            return self._empty_chart("暂无离职数据")

        # 按离职率降序排列
        df = df.sort_values('attrition_rate', ascending=False)

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # 柱状图 - 离职人数（纵向，深蓝色）
        fig.add_trace(
            go.Bar(
                x=df['department'],
                y=df['departure_count'],
                name='离职人数',
                marker_color=self.colors['primary'],
                text=df['departure_count'],
                textposition='outside',
                textfont=dict(size=11, color=self.colors['primary']),
                hovertemplate='<b>%{x}</b><br>离职人数: %{y}人<extra></extra>'
            ),
            secondary_y=False
        )

        # 折线图 - 离职率（红色）
        fig.add_trace(
            go.Scatter(
                x=df['department'],
                y=df['attrition_rate'],
                name='离职率(%)',
                mode='lines+markers+text',
                marker=dict(
                    size=10,
                    color=self.colors['danger'],
                    symbol='circle'
                ),
                line=dict(
                    color=self.colors['danger'],
                    width=2
                ),
                text=[f'{rate:.2f}%' for rate in df['attrition_rate']],
                textposition='top center',
                textfont=dict(size=10, color=self.colors['danger']),
                hovertemplate='<b>%{x}</b><br>离职率: %{y:.2f}%<extra></extra>'
            ),
            secondary_y=True
        )

        fig.update_layout(
            title=dict(
                text='各部门离职情况',
                font=dict(size=16, color='#1F2937'),
                x=0.5
            ),
            height=400,
            margin=dict(t=60, b=80, l=50, r=50),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.08,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0.8)'
            ),
            xaxis=dict(
                title='',
                showgrid=False,
                tickangle=-30,
                tickfont=dict(size=11)
            ),
            yaxis=dict(
                title='离职人数',
                showgrid=True,
                gridwidth=1,
                gridcolor='#E5E7EB',
                zeroline=False
            ),
            yaxis2=dict(
                title='离职率(%)',
                showgrid=False,
                overlaying='y',
                side='right',
                ticksuffix='%'
            )
        )

        return fig

    def create_leave_type_pie_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        创建离职类型分布饼图（降序排列）

        Args:
            df: 离职类型分布数据

        Returns:
            go.Figure: Plotly图表对象
        """
        if df.empty:
            return self._empty_chart("暂无离职类型数据")

        # 降序排列
        df = df.sort_values('count', ascending=False)

        fig = go.Figure()

        fig.add_trace(go.Pie(
            labels=df['category'],
            values=df['count'],
            hole=0.4,
            marker=dict(colors=self.pie_colors[:len(df)]),
            textinfo='label+value+percent',
            textfont=dict(size=12),
            hovertemplate='<b>%{label}</b><br>人数: %{value}人<br>占比: %{percent}<extra></extra>'
        ))

        fig.update_layout(
            title=dict(
                text='离职类型分布',
                font=dict(size=16, color='#1F2937')
            ),
            height=350,
            margin=dict(t=50, b=30, l=30, r=30),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )

        return fig

    def create_tenure_pie_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        创建司龄分布饼图（降序排列）

        Args:
            df: 司龄分布数据

        Returns:
            go.Figure: Plotly图表对象
        """
        if df.empty:
            return self._empty_chart("暂无司龄数据")

        # 降序排列
        df = df.sort_values('count', ascending=False)

        fig = go.Figure()

        fig.add_trace(go.Pie(
            labels=df['category'],
            values=df['count'],
            hole=0.4,
            marker=dict(colors=self.pie_colors[:len(df)]),
            textinfo='label+value+percent',
            textfont=dict(size=12),
            hovertemplate='<b>%{label}</b><br>人数: %{value}人<br>占比: %{percent}<extra></extra>'
        ))

        fig.update_layout(
            title=dict(
                text='离职司龄分布',
                font=dict(size=16, color='#1F2937')
            ),
            height=350,
            margin=dict(t=50, b=30, l=30, r=30),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )

        return fig

    def create_reason_bar_chart(self, df: pd.DataFrame, max_items: int = 10) -> go.Figure:
        """
        创建离职原因柱状图（纵向分布，降序排列）

        Args:
            df: 离职原因分布数据
            max_items: 最大显示条目数

        Returns:
            go.Figure: Plotly图表对象
        """
        if df.empty:
            return self._empty_chart("暂无离职原因数据")

        # 降序排列并限制数量
        df = df.sort_values('count', ascending=False).head(max_items)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df['category'],
            y=df['count'],
            marker_color=self.colors['accent'],
            text=df['count'],
            textposition='outside',
            textfont=dict(size=11, color=self.colors['accent']),
            hovertemplate='<b>%{x}</b><br>人数: %{y}人<extra></extra>'
        ))

        fig.update_layout(
            title=dict(
                text='离职原因分布',
                font=dict(size=16, color='#1F2937'),
                x=0.5
            ),
            xaxis_title='',
            yaxis_title='离职人数',
            height=350,
            margin=dict(l=50, r=50, t=50, b=80),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                showgrid=False,
                tickangle=-30,
                tickfont=dict(size=10)
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E5E7EB',
                zeroline=False
            )
        )

        return fig

    def create_level_bar_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        创建职级分布柱状图（纵向分布，降序排列）

        Args:
            df: 职级分布数据

        Returns:
            go.Figure: Plotly图表对象
        """
        if df.empty:
            return self._empty_chart("暂无职级数据")

        # 降序排列
        df = df.sort_values('count', ascending=False)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df['category'],
            y=df['count'],
            marker_color=self.colors['purple'],
            text=df['count'],
            textposition='outside',
            textfont=dict(size=11, color=self.colors['purple']),
            hovertemplate='<b>%{x}</b><br>人数: %{y}人<extra></extra>'
        ))

        fig.update_layout(
            title=dict(
                text='离职职级分布',
                font=dict(size=16, color='#1F2937'),
                x=0.5
            ),
            xaxis_title='',
            yaxis_title='离职人数',
            height=350,
            margin=dict(l=50, r=50, t=50, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                showgrid=False,
                tickfont=dict(size=11)
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E5E7EB',
                zeroline=False
            )
        )

        return fig

    def create_trend_line_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        创建离职率趋势折线图

        Args:
            df: 月度统计数据

        Returns:
            go.Figure: Plotly图表对象
        """
        if df.empty:
            return self._empty_chart("暂无趋势数据")

        # 格式化月份显示
        df = df.sort_values('month_key')
        month_labels = [m.replace('-', '年') + '月' for m in df['month_key']]

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # 离职率折线
        fig.add_trace(
            go.Scatter(
                x=month_labels,
                y=df['attrition_rate'],
                name='离职率',
                mode='lines+markers+text',
                marker=dict(size=10, color=self.colors['primary']),
                line=dict(width=2, color=self.colors['primary']),
                text=[f'{r:.2f}%' for r in df['attrition_rate']],
                textposition='top center',
                textfont=dict(size=10, color=self.colors['primary'])
            ),
            secondary_y=False
        )

        # 离职人数柱状图
        fig.add_trace(
            go.Bar(
                x=month_labels,
                y=df['departure_count'],
                name='离职人数',
                marker_color=self.colors['secondary'],
                opacity=0.7,
                text=df['departure_count'],
                textposition='outside',
                textfont=dict(size=10)
            ),
            secondary_y=True
        )

        fig.update_layout(
            title=dict(
                text='月度离职趋势',
                font=dict(size=16, color='#1F2937')
            ),
            height=350,
            margin=dict(t=50, b=50, l=50, r=50),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(showgrid=False),
            yaxis=dict(
                title='离职率 (%)',
                showgrid=True,
                gridwidth=1,
                gridcolor='#E5E7EB',
                ticksuffix='%'
            ),
            yaxis2=dict(
                title='离职人数',
                showgrid=False,
                overlaying='y',
                side='right'
            )
        )

        return fig

    def create_metric_card(self, label: str, value: str, delta: str = None,
                          delta_color: str = 'normal') -> go.Figure:
        """
        创建指标卡片（用于展示关键数据）

        Args:
            label: 指标名称
            value: 指标值
            delta: 变化值
            delta_color: 变化颜色

        Returns:
            go.Figure: Plotly图表对象
        """
        fig = go.Figure()

        # 添加背景色块
        fig.add_trace(go.Scatter(
            x=[0, 1, 1, 0, 0],
            y=[0, 0, 1, 1, 0],
            fill='toself',
            fillcolor='white',
            line=dict(color='white'),
            showlegend=False,
            hoverinfo='none'
        ))

        fig.update_layout(
            height=100,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )

        return fig

    def _empty_chart(self, message: str) -> go.Figure:
        """
        创建空图表

        Args:
            message: 提示信息

        Returns:
            go.Figure: Plotly图表对象
        """
        fig = go.Figure()

        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color='#9CA3AF')
        )

        fig.update_layout(
            height=300,
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )

        return fig

    def get_chart_html(self, fig: go.Figure) -> str:
        """
        获取图表的HTML代码

        Args:
            fig: Plotly图表对象

        Returns:
            str: HTML代码
        """
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
