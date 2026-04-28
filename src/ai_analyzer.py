"""
AI分析模块 - 调用Groq免费大模型进行离职数据分析
"""

import os
from typing import Dict, List, Optional
import pandas as pd
import streamlit as st


class AIAnalyzer:
    """AI离职数据分析器"""

    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        """
        初始化AI分析器

        Args:
            api_key: Groq API密钥（可从环境变量或配置文件获取）
            model: 使用的模型名称
        """
        self.api_key = api_key or os.environ.get('GROQ_API_KEY', '')
        self.model = model
        self.client = None

        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except ImportError:
                st.warning("请安装groq库: pip install groq")
            except Exception as e:
                st.error(f"Groq API初始化失败: {str(e)}")

    def is_available(self) -> bool:
        """
        检查AI功能是否可用

        Returns:
            bool: 是否可用
        """
        return self.client is not None

    def analyze_attrition(self,
                         monthly_stats: pd.DataFrame,
                         dept_stats: pd.DataFrame,
                         departures_df: pd.DataFrame,
                         month_key: str) -> str:
        """
        使用AI分析离职数据

        Args:
            monthly_stats: 月度统计数据
            dept_stats: 部门统计数据
            departures_df: 离职明细
            month_key: 分析月份

        Returns:
            str: AI分析报告
        """
        if not self.is_available():
            return self._generate_mock_analysis(monthly_stats, dept_stats, departures_df, month_key)

        # 构建提示词
        prompt = self._build_analysis_prompt(monthly_stats, dept_stats, departures_df, month_key)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """你是一位专业的HR数据分析专家，专门分析员工离职数据并提供深度洞察。
请用专业、客观的语气分析数据，用中文输出结构清晰的分析报告。"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            return response.choices[0].message.content

        except Exception as e:
            st.error(f"AI分析失败: {str(e)}")
            return self._generate_mock_analysis(monthly_stats, dept_stats, departures_df, month_key)

    def _build_analysis_prompt(self,
                               monthly_stats: pd.DataFrame,
                               dept_stats: pd.DataFrame,
                               departures_df: pd.DataFrame,
                               month_key: str) -> str:
        """
        构建分析提示词

        Args:
            monthly_stats: 月度统计
            dept_stats: 部门统计
            departures_df: 离职明细
            month_key: 月份

        Returns:
            str: 提示词
        """
        prompt_parts = []

        # 公司整体数据
        current_month = monthly_stats[monthly_stats['month_key'] == month_key]
        if not current_month.empty:
            row = current_month.iloc[0]
            prompt_parts.append(f"""【公司整体数据】
- 分析月份：{month_key.replace('-', '年')}月
- 平均人数：{int(row['avg_count'])}人
- 离职人数：{int(row['departure_count'])}人
- 整体离职率：{row['attrition_rate']:.2f}%

""")

        # 累计数据
        if len(monthly_stats) > 1:
            total_departures = monthly_stats['departure_count'].sum()
            avg_rate = monthly_stats['attrition_rate'].mean()
            prompt_parts.append(f"- 1-{month_key.split('-')[1]}月累计离职：{int(total_departures)}人")
            prompt_parts.append(f"- 累计平均离职率：{avg_rate:.2f}%\n")

        # 各部门数据
        if not dept_stats.empty:
            dept_data = dept_stats.sort_values('attrition_rate', ascending=False)
            prompt_parts.append("【各部门数据】")
            for _, dept in dept_data.head(10).iterrows():
                prompt_parts.append(
                    f"- {dept['department']}：离职{int(dept['departure_count'])}人，离职率{dept['attrition_rate']:.2f}%"
                )
            prompt_parts.append("")

        # 离职类型分布
        if not departures_df.empty and 'leave_type' in departures_df.columns:
            type_counts = departures_df['leave_type'].value_counts()
            total = len(departures_df)
            prompt_parts.append("【离职类型分布】")
            for leave_type, count in type_counts.items():
                pct = count / total * 100
                prompt_parts.append(f"- {leave_type}：{int(count)}人，占比{pct:.1f}%")
            prompt_parts.append("")

        # 司龄分布
        if not departures_df.empty and 'tenure_category' in departures_df.columns:
            tenure_counts = departures_df['tenure_category'].value_counts()
            prompt_parts.append("【司龄分布】")
            for category, count in tenure_counts.items():
                pct = count / total * 100
                prompt_parts.append(f"- {category}：{int(count)}人，占比{pct:.1f}%")
            prompt_parts.append("")

        # 离职原因分布
        if not departures_df.empty and 'leave_reason' in departures_df.columns:
            reason_counts = departures_df['leave_reason'].value_counts().head(10)
            prompt_parts.append("【离职原因分布（前10）】")
            for reason, count in reason_counts.items():
                pct = count / total * 100
                prompt_parts.append(f"- {reason}：{int(count)}人，占比{pct:.1f}%")
            prompt_parts.append("")

        # 职级分布
        if not departures_df.empty and 'level' in departures_df.columns:
            level_counts = departures_df['level'].value_counts()
            prompt_parts.append("【职级分布】")
            for level, count in level_counts.items():
                pct = count / total * 100
                prompt_parts.append(f"- {level}：{int(count)}人，占比{pct:.1f}%")

        # 分析要求
        prompt_parts.append("""
请从以下维度进行分析，要求专业、客观、实用：
1. **整体概况**：本月离职情况概述，与历史对比
2. **重点风险预警**：离职率异常高或流失严重的部门
3. **深层原因分析**：
   - 主动离职占比高的含义
   - 新人/中坚力量流失的暗示
   - 离职原因的深层含义
4. **具体优化建议**：分短期、中期、长期给出可执行的建议

请用中文输出，语言专业，结构清晰。建议使用emoji增加可读性。""")

        return "\n".join(prompt_parts)

    def _generate_mock_analysis(self,
                                monthly_stats: pd.DataFrame,
                                dept_stats: pd.DataFrame,
                                departures_df: pd.DataFrame,
                                month_key: str) -> str:
        """
        生成模拟分析报告（当AI不可用时）

        Args:
            monthly_stats: 月度统计
            dept_stats: 部门统计
            departures_df: 离职明细
            month_key: 月份

        Returns:
            str: 模拟分析报告
        """
        analysis = []

        analysis.append(f"# 📊 AI离职分析报告 - {month_key.replace('-', '年')}月\n")

        # 整体概况
        current_month = monthly_stats[monthly_stats['month_key'] == month_key]
        if not current_month.empty:
            row = current_month.iloc[0]
            analysis.append("## 【📈 整体概况】")
            analysis.append(f"""
本月共离职 **{int(row['departure_count'])}人**，整体离职率为 **{row['attrition_rate']:.2f}%**。
公司平均在岗人数 **{int(row['avg_count'])}人**。

""")

        # 风险预警
        if not dept_stats.empty:
            high_risk = dept_stats[dept_stats['attrition_rate'] > 3.0]
            if not high_risk.empty:
                analysis.append("## 【⚠️ 重点风险预警】\n")
                for _, dept in high_risk.iterrows():
                    analysis.append(f"""
### {dept['department']}
- 离职人数：{int(dept['departure_count'])}人
- 离职率：**{dept['attrition_rate']:.2f}%**
- 建议：需重点关注，分析具体原因并制定保留策略
""")

        # 离职类型分析
        if not departures_df.empty and 'leave_type' in departures_df.columns:
            analysis.append("## 【🔍 离职类型分析】\n")
            type_counts = departures_df['leave_type'].value_counts()
            total = len(departures_df)

            for leave_type, count in type_counts.items():
                pct = count / total * 100
                if leave_type == '主动离职':
                    analysis.append(f"- **主动离职**：{int(count)}人，占比{pct:.1f}%")
                    analysis.append("  - 💡 说明：主动离职多反映员工对公司的认可度或职业发展预期不足\n")
                elif leave_type == '被动离职':
                    analysis.append(f"- **被动离职**：{int(count)}人，占比{pct:.1f}%")
                    analysis.append("  - 💡 说明：被动离职可能涉及绩效管理或组织调整问题\n")

        # 司龄分析
        if not departures_df.empty and 'tenure_category' in departures_df.columns:
            analysis.append("## 【👥 司龄分布分析】\n")
            tenure_counts = departures_df['tenure_category'].value_counts()

            for category, count in tenure_counts.items():
                pct = count / total * 100
                if category in ['新人', '0-0.5年']:
                    analysis.append(f"- **{category}**：{int(count)}人，占比{pct:.1f}%")
                    analysis.append("  - 💡 需关注：新人流失可能影响团队稳定性和培养成本\n")
                elif category in ['中坚', '1-3年']:
                    analysis.append(f"- **{category}**：{int(count)}人，占比{pct:.1f}%")
                    analysis.append("  - 💡 需关注：中坚力量流失可能导致人才断层\n")

        # 优化建议
        analysis.append("""
## 【💡 综合优化建议】

### 短期措施（1个月内）
1. 对高离职率部门进行满意度调研
2. 优化新员工入职体验，加强第一周关怀
3. 建立离职预警机制，提前干预高风险员工

### 中期措施（3个月内）
1. 梳理并优化职级晋升通道
2. 建立中坚员工保留计划
3. 优化招聘环节，强化岗位匹配度评估

### 长期措施（6个月内）
1. 进行薪酬市场对标，优化薪酬竞争力
2. 建立人才梯队，避免关键岗位断层
3. 定期复盘离职数据，持续优化管理策略

---
*⚠️ 提示：配置Groq API密钥可获得更精准的AI分析。请访问 https://console.groq.com/ 免费获取密钥。*
""")

        return "\n".join(analysis)

    def generate_insights_summary(self, analysis_report: str) -> List[Dict]:
        """
        从分析报告中提取关键洞察

        Args:
            analysis_report: AI分析报告

        Returns:
            List[Dict]: 关键洞察列表
        """
        insights = []

        # 简单提取包含关键信息的行
        lines = analysis_report.split('\n')
        for line in lines:
            if '⚠️' in line or '💡' in line or '高风险' in line or '建议' in line:
                if line.strip():
                    insights.append({
                        'type': 'warning' if '⚠️' in line else 'suggestion',
                        'content': line.strip()
                    })

        return insights[:10]  # 最多返回10条
