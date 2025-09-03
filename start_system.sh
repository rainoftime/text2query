#!/bin/bash

# 启动整个系统的脚本

echo "=============================================="
echo "启动Semgrep规则引擎多智能体系统"
echo "=============================================="

# 检查Ollama是否运行
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "启动Ollama..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 5  # 给启动时间
fi

# 检查模型是否已加载
if ! ollama list | grep -q "deepseek-coder:6.7b"; then
    echo "加载模型 deepseek-coder:6.7b..."
    ollama pull deepseek-coder:6.7b
fi

# 激活虚拟环境
source venv_autogen/bin/activate

# 启动主系统
echo "启动主系统..."
python main.py

# 如果我们启动了Ollama，停止它
if [ ! -z "$OLLAMA_PID" ]; then
    echo "停止Ollama..."
    kill $OLLAMA_PID
fi