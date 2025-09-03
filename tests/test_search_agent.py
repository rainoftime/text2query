#!/usr/bin/env python3
"""
测试搜索智能体。
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.vector_db_manager import VectorDBManager
from agents.search_agent import SearchAgent
from config.llm_config import LLM_CONFIG

def test_search_agent():
    """测试搜索智能体。"""
    print("初始化VectorDBManager...")
    vector_db_manager = VectorDBManager()
    
    print("初始化SearchAgent...")
    search_agent = SearchAgent(LLM_CONFIG, vector_db_manager)
    
    # 测试用例
    test_cases = [
        "代码中存在通过字符串连接的SQL注入",
        "使用了弱MD5哈希算法",
        "通过innerHTML存在XSS可能性",
        "代码中硬编码了密钥",
        "不安全的反序列化数据"
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'='*50}")
        print(f"测试 {i+1}: {test_case}")
        print(f"{'='*50}")
        
        result = search_agent.find_relevant_rules(test_case)
        print(result)

if __name__ == "__main__":
    test_search_agent()