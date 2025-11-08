# AgentNote: The Notebook Playground for Autonomous Agents

## 🧠 核心理念

AgentNote项目致力于打造这样一个工具，在这里AI智能体能够自主探索、实验和学习。与此同时，所有的思考和执行过程，都自动化的沉淀为可以重复执行的notebook，能够有效提升智能体执行决策的可读性、可信性、可复用性。

## 🛠️ 项目结构

```
AgentNote/
├── README.md                   # 项目说明文档
├── main.py                     # 程序主入口
├── __init__.py                 # 根目录包初始化
│
├── agents/                     # 智能体核心模块
│   ├── __init__.py             # 智能体模块初始化
│   └── note_agent.py           # 主智能体类 - 任务协调和状态管理
│
├── core/                       # 核心功能模块
│   ├── __init__.py             # 核心模块初始化
│   ├── config.py               # 配置管理 - 全局配置数据类
│   ├── deepseek_client.py      # DeepSeek API交互
│   ├── content_parser.py       # 内容解析器 - 代码和文本分离
│   ├── notebook_manager.py     # Notebook管理器 - 文件操作和上下文管理
│   ├── notebook_generator.py   # Notebook生成器 - Cell创建和格式化
│   ├── notebook_exporter.py    # Notebook导出器 - 数据导出和序列化
│   ├── executor.py             # 执行器 - 代码安全执行和错误处理
│   └── state_manager.py        # 状态管理器 - 执行状态跟踪
│
├── prompts/                    # 提示词模板
│   └── prompts.yaml            # 智能体提示词配置 - 系统提示词和任务模板
│
├── utils/                      # 工具函数
│   ├── __init__.py             # 工具模块初始化
│   ├── config_loader.py        # 配置加载器 - YAML配置读写
│   └── config.yaml             # 主配置文件 - 项目运行参数
```

## 📄 许可证

本项目将采用 MIT 许可证。


**开始您的智能体认知探索之旅吧！** 🚀

*让AI智能体在Notebook的游乐场中自由探索、学习和创造*