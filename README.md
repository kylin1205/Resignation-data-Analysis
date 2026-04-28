# 员工离职数据分析系统

基于Streamlit的离职数据分析系统，支持Excel数据导入、离职率计算、可视化分析和AI智能洞察。

## 功能特性

- 📁 **数据导入**：支持Excel文件上传，自动解析期初/期末/离职数据
- 📊 **离职率计算**：自动计算月度/累计离职率，支持部门级别统计
- 📈 **可视化分析**：6种图表类型（柱状图、饼图、折线图），全部降序排列
- 🤖 **AI智能分析**：集成Groq免费大模型，自动生成深度洞察报告
- 📥 **数据导出**：支持导出Excel和PDF分析报告
- 📅 **多月份分析**：支持历史数据累积和月份筛选

## 技术栈

- **前端框架**: Streamlit
- **数据处理**: Pandas, NumPy
- **可视化**: Plotly
- **数据库**: SQLite
- **PDF导出**: ReportLab
- **AI服务**: Groq API (免费)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

### 3. 部署到Streamlit Cloud

1. 将代码推送到GitHub仓库
2. 访问 [share.streamlit.io](https://share.streamlit.io/)
3. 连接GitHub仓库并部署

## 配置说明

### AI功能（可选）

要启用AI分析功能，需要配置Groq API密钥：

1. 访问 [Groq Console](https://console.groq.com/) 免费注册
2. 创建API密钥
3. 设置环境变量：

```bash
export GROQ_API_KEY="your-api-key"
```

或者在Streamlit Cloud的Secrets中配置：

```toml
GROQ_API_KEY = "your-api-key"
```

## Excel文件格式

系统期望的Excel文件包含以下Sheet：

| Sheet名称 | 说明 | 必需字段 |
|-----------|------|---------|
| X月期初人数 | 当月在职人员名单 | 工号、姓名、部门 |
| X月离职数据 | 当月离职人员名单 | 工号、离职类型、离职原因 |

## 离职率计算

```
月度离职率 = 当月离职人数 / 当月平均人数 × 100%
当月平均人数 = (上月期末人数 + 当月期末人数) / 2
```

## 项目结构

```
employee-attrition-analysis/
├── app.py                 # Streamlit主应用
├── config.yaml            # 配置文件
├── requirements.txt        # 依赖清单
├── README.md              # 项目说明
├── data/                  # 数据目录
├── src/                   # 源代码
│   ├── data_loader.py     # 数据加载
│   ├── data_processor.py  # 数据处理
│   ├── analytics.py       # 分析计算
│   ├── charts.py         # 图表生成
│   ├── database.py       # 数据库
│   ├── ai_analyzer.py    # AI分析
│   └── exporter.py        # 导出功能
└── prompts/              # AI提示词
```

## License

MIT License
