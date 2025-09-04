#!/bin/bash

# Semgrep规则引擎多智能体系统的安装和配置脚本
# 适用于Ubuntu 22.04 LTS

set -e  # 出错时中断执行

echo "=============================================="
echo "安装Semgrep规则引擎多智能体系统"
echo "=============================================="

# 输出颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查命令执行成功性的函数
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}成功!${NC}"
    else
        echo -e "${RED}错误!${NC}"
        exit 1
    fi
}

# 带检查的包安装函数
install_package() {
    echo -n "安装 $1... "
    sudo apt-get install -y $1 > /dev/null 2>&1
    check_success
}

# 更新系统
echo -n "更新包列表... "
sudo apt-get update > /dev/null 2>&1
check_success

# 安装必要的系统包
echo "安装系统依赖..."
install_package python3.11
install_package python3.11-venv
install_package python3-pip
install_package curl
install_package wget
install_package git

# 安装Ollama
echo -n "安装Ollama... "
curl -fsSL https://ollama.ai/install.sh | sh > /dev/null 2>&1
check_success

# 启动Ollama服务
echo -n "启动Ollama服务... "
sudo systemctl start ollama > /dev/null 2>&1
sudo systemctl enable ollama > /dev/null 2>&1
check_success

# 加载deepseek-coder模型
echo -n "加载模型 deepseek-coder:6.7b... "
ollama pull deepseek-coder:6.7b > /dev/null 2>&1 &
OLAMA_PID=$!
# 等待加载完成，带超时
sleep 30
if ps -p $OLAMA_PID > /dev/null; then
    echo -e "${YELLOW}模型加载仍在后台进行...${NC}"
else
    check_success
fi

# 创建Python虚拟环境
echo -n "创建虚拟环境... "
python3.11 -m venv venv_autogen > /dev/null 2>&1
check_success

# 激活虚拟环境
echo -n "激活虚拟环境... "
source venv_autogen/bin/activate
check_success

# 安装Python依赖
echo -n "安装Python依赖... "
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
check_success

# 创建文件夹结构
echo -n "创建文件夹结构... "
mkdir -p data/raw_rules data/generated_rules logs tests scripts agents core utils config > /dev/null 2>&1
check_success

# 克隆官方Semgrep规则仓库
echo -n "克隆官方semgrep-rules仓库... "
git clone https://github.com/semgrep/semgrep-rules.git data/official_rules > /dev/null 2>&1
check_success

# 将规则复制到raw_rules
echo -n "将官方规则复制到工作目录... "
cp -r data/official_rules/* data/raw_rules/ > /dev/null 2>&1
check_success

# 删除临时文件（可选）
echo -n "清理临时文件... "
rm -rf data/official_rules/.git data/official_rules/README.md > /dev/null 2>&1
check_success

# 构建向量数据库
echo -n "构建向量数据库... "
python scripts/build_vector_db.py > /dev/null 2>&1
check_success

# 运行测试
echo "运行测试..."
echo "1. 测试搜索智能体..."
python tests/test_search_agent.py

echo "2. 测试规则工程师智能体..."
python tests/test_rule_engineer_agent.py

echo "3. 测试验证智能体..."
python tests/test_validation_agent.py

echo "4. 测试完整工作流程..."
python tests/test_full_workflow.py

echo "=============================================="
echo -e "${GREEN}安装和配置完成！${NC}"
echo "=============================================="
echo ""
echo "要启动系统，请执行："
echo "  source venv_autogen/bin/activate"
echo "  python main.py"
echo ""
echo "要启动Ollama（如果未运行）："
echo "  ollama serve"
echo "  ollama run deepseek-coder:6.7b"
echo ""
echo "要停止Ollama："
echo "  sudo systemctl stop ollama"
echo "=============================================="