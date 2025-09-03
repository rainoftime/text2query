# Itero 🛠️

Itero is a multi-agent LLM system designed to automate the creation and updating of static code analysis rules for Semgrep. By describing a vulnerability in natural language, Itero intelligently searches for existing patterns, crafts new precise rules, and validates them against your code—dramatically reducing the manual effort required for security tooling maintenance.

## Key Features

*   **🤖 Multi-Agent Architecture:** Leverages Microsoft's AutoGen to orchestrate specialized AI agents for analysis, search, engineering, and validation.
*   **🔍 Semantic Rule Search:** Utilizes RAG (Retrieval-Augmented Generation) with ChromaDB to find relevant existing rules from your codebase.
*   **✍️ Intelligent Rule Generation:** Empowers a local LLM (via Ollama) to write and update high-quality Semgrep YAML rules based on natural language descriptions and code examples.
*   **✅ Integrated Validation:** Automatically tests generated rules using the Semgrep CLI to ensure they trigger correctly and avoid false positives.
*   **💻 Developer-Centric:** Designed as a local-first prototype, giving you full control over your code and data without relying on external APIs.

## 项目高层架构 (Component Diagram)

Web界面和后端用虚线框表示，作为未来组件。
系统核心是您当前正在开发的主要模块。
智能体通过AutoGen的Group Chat机制相互通信。
智能体通过Function Call机制与工具（缓存、数据库管理器、Semgrep运行器）交互（智能体说明需要什么函数，User Proxy Agent执行它）。
工具与底层组件交互：文件系统（日志、数据库）和系统调用（Semgrep CLI）。
本地LLM（Ollama）作为独立服务运行，所有智能体通过API访问它。

<img width="513" height="698" alt="image" src="https://github.com/user-attachments/assets/fa904b0a-0039-4a19-bd46-e19ac7253c61" />

## 关键数据流：

### 搜索流程：

[数据] 漏洞文本描述 -> 协调智能体 -> 搜索智能体
[函数调用] 搜索智能体 -> 向量数据库管理器 -> [查询] -> ChromaDB
[数据] ChromaDB -> [JSON结果] -> 向量数据库管理器 -> 搜索智能体 -> 协调智能体

### 生成流程：

[数据] 源代码 + 描述 + (可选找到的规则) -> 协调智能体 -> 工程师智能体
[函数调用] 工程师智能体形成提示 -> [HTTP请求] -> Ollama API
[数据] Ollama API -> [生成的文本] -> 工程师智能体 (尝试提取YAML)
[数据] 生成的YAML -> 工程师智能体 -> 协调智能体

### 验证流程：

[数据] 生成的YAML + 源代码 -> 协调智能体 -> 验证智能体
[函数调用] 验证智能体 -> Semgrep运行器 -> [系统调用] -> Semgrep CLI
[数据] Semgrep CLI -> [标准输出/错误输出] -> Semgrep运行器 (解析JSON)
[数据] 解析结果 (成功/错误) -> 验证智能体 -> 协调智能体


使用说明：

1. chmod +x setup_ubuntu.sh run_tests.sh start_system.sh
2. ./setup_ubuntu.sh ./run_tests.sh ./start_system.sh


### 更新规则

要更新规则到最新版本，请执行：

python scripts/update_rules.py