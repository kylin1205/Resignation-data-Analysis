"""
员工离职数据分析系统 - Streamlit主应用
"""

import streamlit as st
import pandas as pd
import os
import yaml
from io import BytesIO

# 导入自定义模块
from src.data_loader import DataLoader
from src.data_processor import DataProcessor
from src.analytics import Analytics
from src.charts import ChartGenerator
from src.database import Database
from src.ai_analyzer import AIAnalyzer
from src.exporter import Exporter


# 页面配置
st.set_page_config(
    page_title="员工离职数据分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 隐藏Streamlit默认样式
st.markdown("""
<style>
    /* 隐藏默认header */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 指标卡片样式 */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4F46E5;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6B7280;
        margin-top: 5px;
    }

    /* 图表容器 */
    .chart-container {
        background: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* AI分析框 */
    .ai-analysis {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
    }

    /* 风险标签 */
    .risk-high {color: #EF4444; font-weight: bold;}
    .risk-medium {color: #F59E0B; font-weight: bold;}
    .risk-low {color: #10B981; font-weight: bold;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_config():
    """加载配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def init_session_state():
    """初始化会话状态"""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'employees_df' not in st.session_state:
        st.session_state.employees_df = pd.DataFrame()
    if 'departures_df' not in st.session_state:
        st.session_state.departures_df = pd.DataFrame()
    if 'monthly_stats' not in st.session_state:
        st.session_state.monthly_stats = pd.DataFrame()
    if 'available_months' not in st.session_state:
        st.session_state.available_months = []
    if 'ai_analysis' not in st.session_state:
        st.session_state.ai_analysis = None


def main():
    """主函数"""
    # 初始化
    init_session_state()
    config = load_config()

    # 标题
    st.title("📊 员工离职数据分析系统")
    st.markdown("---")

    # 侧边栏 - 数据导入
    with st.sidebar:
        st.header("📁 数据导入")

        # 上传文件
        uploaded_file = st.file_uploader(
            "选择Excel文件",
            type=['xlsx', 'xls'],
            help="支持.xlsx和.xls格式的Excel文件"
        )

        if uploaded_file:
            if st.button("🚀 导入数据", type="primary", use_container_width=True):
                with st.spinner("正在处理数据..."):
                    try:
                        # 加载数据
                        loader = DataLoader()
                        sheets = loader.load_excel(uploaded_file)

                        if not sheets:
                            st.error("❌ 无法读取Excel文件，请检查文件格式")
                            return

                        st.info(f"📋 检测到 {len(sheets)} 个Sheet")

                        # 处理每个Sheet，根据Sheet名称确定月份映射
                        processor = DataProcessor()
                        all_employees = []
                        all_departures = []
                        processed_sheets = set()

                        for sheet_name, df in sheets.items():
                            if sheet_name in processed_sheets:
                                continue

                            mapping = loader.get_sheet_month_mapping(sheet_name)
                            sheet_type = loader.parse_sheet_type(sheet_name, df)

                            if '离职' in mapping:
                                # 离职数据Sheet - 从离职日期推断月份
                                departures = loader.extract_departures(df, 'unknown')
                                departures = processor.clean_departure_data(departures)
                                departures = processor.calculate_tenure(departures)
                                departures = processor.categorize_tenure(departures)

                                # 从离职日期推断月份
                                if 'leave_date' in departures.columns:
                                    departures['leave_date'] = pd.to_datetime(departures['leave_date'], errors='coerce')
                                    departures['month_key'] = departures['leave_date'].dt.strftime('%Y-%m')
                                    # 只保留有效月份的行
                                    departures = departures[departures['month_key'].notna() & (departures['month_key'] != 'NaT')]

                                all_departures.append(departures)
                                processed_sheets.add(sheet_name)

                            else:
                                # 期初/期末人员Sheet
                                for role, month_key in mapping.items():
                                    employees = loader.extract_employees(df, month_key, role)
                                    employees = processor.clean_employee_data(employees)
                                    employees = processor.categorize_tenure(employees)
                                    employees['role'] = role  # 标记是期初还是期末
                                    all_employees.append(employees)
                                processed_sheets.add(sheet_name)

                        # 合并数据
                        if all_employees:
                            st.session_state.employees_df = pd.concat(all_employees, ignore_index=True)
                        if all_departures:
                            st.session_state.departures_df = pd.concat(all_departures, ignore_index=True)

                        # 计算月度统计
                        if not st.session_state.employees_df.empty:
                            st.session_state.monthly_stats = processor.prepare_monthly_summary(
                                st.session_state.employees_df,
                                st.session_state.departures_df
                            )

                        # 只保留有期末数据的月份（排除只有期初数据的情况如4月）
                        valid_months = []
                        for month in sorted(st.session_state.employees_df['month_key'].unique()):
                            has_start = len(st.session_state.employees_df[
                                (st.session_state.employees_df['month_key'] == month) &
                                (st.session_state.employees_df['role'] == '期初')
                            ]) > 0
                            has_end = len(st.session_state.employees_df[
                                (st.session_state.employees_df['month_key'] == month) &
                                (st.session_state.employees_df['role'] == '期末')
                            ]) > 0
                            if has_start and has_end:
                                valid_months.append(month)

                        st.session_state.available_months = valid_months

                        st.session_state.data_loaded = True
                        st.success(f"✅ 数据导入成功！导入 {len(st.session_state.employees_df)} 条人员记录，{len(st.session_state.departures_df)} 条离职记录")

                    except Exception as e:
                        import traceback
                        st.error(f"❌ 数据导入失败: {str(e)}")

        # 清除数据
        if st.session_state.data_loaded:
            st.markdown("---")
            if st.button("🗑️ 清除所有数据", use_container_width=True):
                st.session_state.data_loaded = False
                st.session_state.employees_df = pd.DataFrame()
                st.session_state.departures_df = pd.DataFrame()
                st.session_state.monthly_stats = pd.DataFrame()
                st.session_state.available_months = []
                st.session_state.ai_analysis = None
                st.rerun()

    # 主内容区
    if not st.session_state.data_loaded:
        # 欢迎页面
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 50px 20px;">
                <h2>👋 欢迎使用员工离职数据分析系统</h2>
                <p style="color: #6B7280; margin-top: 20px;">
                    请在左侧上传包含期初/期末人数和离职数据的Excel文件开始分析
                </p>

                <div style="margin-top: 40px; text-align: left; background: #F3F4F6; padding: 20px; border-radius: 10px;">
                    <h4>📋 Excel文件应包含以下Sheet：</h4>
                    <ul style="color: #4B5563;">
                        <li><b>期初人数Sheet</b>：如"1月期初人数"、"2月期初人数"</li>
                        <li><b>离职数据Sheet</b>：如"离职数据"</li>
                    </ul>

                    <h4 style="margin-top: 20px;">🔢 系统将自动计算：</h4>
                    <ul style="color: #4B5563;">
                        <li>月度离职率 = 离职人数 / 平均人数 × 100%</li>
                        <li>平均人数 = (期初人数 + 期末人数) / 2</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
        return

    # 数据加载后的主界面
    processor = DataProcessor()
    analytics = Analytics()
    chart_gen = ChartGenerator()

    # 月份选择
    st.markdown("### 📅 选择分析月份")
    selected_month = st.selectbox(
        "选择要分析的月份",
        options=st.session_state.available_months,
        format_func=lambda x: x.replace('-', '年') + '月',
        index=len(st.session_state.available_months) - 1 if st.session_state.available_months else 0
    )

    if not selected_month:
        st.warning("请先导入数据")
        return

    # 获取当前月数据
    monthly_data = st.session_state.monthly_stats[
        st.session_state.monthly_stats['month_key'] == selected_month
    ]

    if monthly_data.empty:
        st.warning("该月份暂无数据")
        return

    month_row = monthly_data.iloc[0]

    # ===== 关键指标卡片 =====
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="📈 平均人数",
            value=f"{int(month_row['avg_count'])}人",
            help="当月平均在岗人数"
        )

    with col2:
        st.metric(
            label="👥 离职人数",
            value=f"{int(month_row['departure_count'])}人",
            help="当月离职员工总数"
        )

    with col3:
        rate = month_row['attrition_rate']
        delta = None
        if len(st.session_state.monthly_stats) > 1:
            prev = st.session_state.monthly_stats[
                st.session_state.monthly_stats['month_key'] < selected_month
            ]
            if not prev.empty:
                prev_rate = prev.iloc[-1]['attrition_rate']
                delta = f"{rate - prev_rate:.2f}%"

        st.metric(
            label="📊 离职率",
            value=f"{rate:.2f}%",
            delta=delta,
            help="离职人数 / 平均人数 × 100%"
        )

    # ===== AI智能分析 =====
    st.markdown("---")
    st.markdown("### 🤖 AI智能分析")

    # 获取AI API密钥
    groq_api_key = os.environ.get('GROQ_API_KEY', '')
    ai_analyzer = AIAnalyzer(api_key=groq_api_key)

    if st.button("🔍 生成AI分析报告", type="primary"):
        with st.spinner("正在调用AI分析，请稍候..."):
            # 获取部门统计
            dept_stats = processor.aggregate_department_stats(
                st.session_state.employees_df,
                st.session_state.departures_df,
                selected_month
            )

            # 获取离职明细
            departures = st.session_state.departures_df[
                st.session_state.departures_df['month_key'] == selected_month
            ]

            # 调用AI分析
            st.session_state.ai_analysis = ai_analyzer.analyze_attrition(
                st.session_state.monthly_stats,
                dept_stats,
                departures,
                selected_month
            )

    if st.session_state.ai_analysis:
        st.markdown(st.session_state.ai_analysis)

    # ===== 可视化图表 =====
    st.markdown("---")
    st.markdown("### 📈 数据可视化分析")

    # 计算部门统计
    dept_stats = processor.aggregate_department_stats(
        st.session_state.employees_df,
        st.session_state.departures_df,
        selected_month
    )

    # 添加风险等级
    overall_rate = month_row['attrition_rate']
    dept_stats = analytics.analyze_department_attrition(dept_stats, overall_rate)

    # 离职明细
    departures = st.session_state.departures_df[
        st.session_state.departures_df['month_key'] == selected_month
    ]

    # 1. 部门分析 - 柱状图 + 折线图
    st.markdown("#### 各部门离职情况")
    col1, col2 = st.columns(2)

    with col1:
        if not dept_stats.empty:
            fig_bar = chart_gen.create_department_bar_chart(dept_stats)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("暂无部门数据")

    with col2:
        if not dept_stats.empty:
            fig_line = chart_gen.create_department_line_chart(dept_stats)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("暂无离职率数据")

    # 2. 离职类型 + 司龄分布 - 饼图
    st.markdown("#### 离职类型与司龄分布")
    col1, col2 = st.columns(2)

    with col1:
        leave_type_dist = processor.get_departure_distribution(departures, selected_month, 'leave_type')
        fig_pie_type = chart_gen.create_leave_type_pie_chart(leave_type_dist)
        st.plotly_chart(fig_pie_type, use_container_width=True)

    with col2:
        tenure_dist = processor.get_departure_distribution(departures, selected_month, 'tenure_category')
        # 排序
        if not tenure_dist.empty:
            tenure_order = ['0-0.5年', '0.5-1年', '1-3年', '3-5年', '5年以上']
            tenure_dist['sort_order'] = tenure_dist['category'].map(
                {v: i for i, v in enumerate(tenure_order)}
            )
            tenure_dist = tenure_dist.sort_values('sort_order').drop('sort_order', axis=1)
        fig_pie_tenure = chart_gen.create_tenure_pie_chart(tenure_dist)
        st.plotly_chart(fig_pie_tenure, use_container_width=True)

    # 3. 离职原因 + 职级分布 - 柱状图
    st.markdown("#### 离职原因与职级分布")
    col1, col2 = st.columns(2)

    with col1:
        reason_dist = processor.get_departure_distribution(departures, selected_month, 'leave_reason')
        fig_reason = chart_gen.create_reason_bar_chart(reason_dist)
        st.plotly_chart(fig_reason, use_container_width=True)

    with col2:
        level_dist = processor.get_departure_distribution(departures, selected_month, 'level')
        fig_level = chart_gen.create_level_bar_chart(level_dist)
        st.plotly_chart(fig_level, use_container_width=True)

    # 4. 趋势分析
    if len(st.session_state.monthly_stats) > 1:
        st.markdown("#### 月度离职趋势")
        fig_trend = chart_gen.create_trend_line_chart(st.session_state.monthly_stats)
        st.plotly_chart(fig_trend, use_container_width=True)

    # ===== 离职人员明细 =====
    st.markdown("---")
    st.markdown("### 📋 离职人员明细")

    details = processor.get_departure_details(st.session_state.departures_df, selected_month)

    if not details.empty:
        st.dataframe(
            details,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        st.caption(f"共 {len(details)} 条离职记录")
    else:
        st.info("该月份暂无离职记录")

    # ===== 数据导出 =====
    st.markdown("---")
    st.markdown("### 📥 导出报告")

    col1, col2 = st.columns(2)
    exporter = Exporter()

    with col1:
        if st.button("📊 导出Excel", use_container_width=True):
            excel_file = exporter.export_to_excel(
                st.session_state.monthly_stats,
                dept_stats,
                departures,
                selected_month
            )
            st.download_button(
                label="下载Excel文件",
                data=excel_file,
                file_name=exporter.generate_excel_filename(selected_month),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    with col2:
        if st.button("📄 导出PDF报告", use_container_width=True):
            pdf_file = exporter.export_to_pdf(
                st.session_state.monthly_stats,
                dept_stats,
                departures,
                selected_month,
                st.session_state.ai_analysis
            )
            st.download_button(
                label="下载PDF文件",
                data=pdf_file,
                file_name=exporter.generate_pdf_filename(selected_month),
                mime="application/pdf",
                use_container_width=True
            )

    # 页脚
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #9CA3AF; font-size: 12px;'>"
        "员工离职数据分析系统 | Powered by Streamlit & AI"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
