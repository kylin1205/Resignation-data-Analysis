"""
AI分析提示词模板
"""

ANALYSIS_PROMPT_TEMPLATE = """
你是专业的HR数据分析专家。请分析以下离职数据，并给出深度洞察：

【公司整体数据】
- 分析月份：{month}
- 平均人数：{avg_count}人
- 离职人数：{departure_count}人
- 整体离职率：{attrition_rate}%

【各部门数据】
{department_data}

【离职类型分布】
{leave_type_data}

【离职原因分布】
{leave_reason_data}

【司龄分布】
{tenure_data}

【职级分布】
{level_data}

请从以下维度进行分析：
1. 整体概况和趋势判断
2. 重点风险预警（离职率异常高/低的部门）
3. 深层原因分析（主动离职、司龄分布等）
4. 具体优化建议

请用中文输出，结构清晰，语言专业。建议使用emoji增加可读性。
"""


def format_department_data(dept_stats):
    """格式化部门数据"""
    if dept_stats.empty:
        return "暂无数据"

    lines = []
    for _, row in dept_stats.iterrows():
        lines.append(f"- {row['department']}：离职{int(row['departure_count'])}人，离职率{row['attrition_rate']:.2f}%")

    return "\n".join(lines)


def format_leave_type_data(departures_df):
    """格式化离职类型数据"""
    if departures_df.empty or 'leave_type' not in departures_df.columns:
        return "暂无数据"

    counts = departures_df['leave_type'].value_counts()
    total = len(departures_df)

    lines = []
    for leave_type, count in counts.items():
        pct = count / total * 100
        lines.append(f"- {leave_type}：{int(count)}人，占比{pct:.1f}%")

    return "\n".join(lines)


def format_leave_reason_data(departures_df, top_n=10):
    """格式化离职原因数据"""
    if departures_df.empty or 'leave_reason' not in departures_df.columns:
        return "暂无数据"

    counts = departures_df['leave_reason'].value_counts().head(top_n)
    total = len(departures_df)

    lines = []
    for reason, count in counts.items():
        pct = count / total * 100
        lines.append(f"- {reason}：{int(count)}人，占比{pct:.1f}%")

    return "\n".join(lines)


def format_tenure_data(departures_df):
    """格式化司龄数据"""
    if departures_df.empty or 'tenure_category' not in departures_df.columns:
        return "暂无数据"

    counts = departures_df['tenure_category'].value_counts()
    total = len(departures_df)

    lines = []
    for category, count in counts.items():
        pct = count / total * 100
        lines.append(f"- {category}：{int(count)}人，占比{pct:.1f}%")

    return "\n".join(lines)


def format_level_data(departures_df):
    """格式化职级数据"""
    if departures_df.empty or 'level' not in departures_df.columns:
        return "暂无数据"

    counts = departures_df['level'].value_counts()
    total = len(departures_df)

    lines = []
    for level, count in counts.items():
        pct = count / total * 100
        lines.append(f"- {level}：{int(count)}人，占比{pct:.1f}%")

    return "\n".join(lines)


def build_analysis_prompt(month_key, avg_count, departure_count, attrition_rate,
                         dept_stats, departures_df):
    """
    构建完整的分析提示词

    Args:
        month_key: 月份
        avg_count: 平均人数
        departure_count: 离职人数
        attrition_rate: 离职率
        dept_stats: 部门统计
        departures_df: 离职明细

    Returns:
        str: 完整的提示词
    """
    return ANALYSIS_PROMPT_TEMPLATE.format(
        month=f"{month_key.replace('-', '年')}月",
        avg_count=int(avg_count),
        departure_count=int(departure_count),
        attrition_rate=attrition_rate,
        department_data=format_department_data(dept_stats),
        leave_type_data=format_leave_type_data(departures_df),
        leave_reason_data=format_leave_reason_data(departures_df),
        tenure_data=format_tenure_data(departures_df),
        level_data=format_level_data(departures_df)
    )
