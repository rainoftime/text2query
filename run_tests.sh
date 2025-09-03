#!/bin/bash

# 运行所有测试的脚本

set -e  # 出错时中断执行

echo "=============================================="
echo "运行多智能体系统测试"
echo "=============================================="

# 激活虚拟环境
source venv_autogen/bin/activate

# 运行测试
echo "1. 运行搜索智能体测试..."
python tests/test_search_agent.py

echo ""
echo "2. 运行规则工程师智能体测试..."
python tests/test_rule_engineer_agent.py

echo ""
echo "3. 运行验证智能体测试..."
python tests/test_validation_agent.py

echo ""
echo "4. 运行完整工作流程测试..."
python tests/test_full_workflow.py

echo ""
echo "=============================================="
echo "所有测试完成!"
echo "=============================================="