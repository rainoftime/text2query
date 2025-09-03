#!/usr/bin/env python3
"""
测试规则工程师智能体。
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.rule_engineer_agent import RuleEngineerAgent
from config.llm_config import LLM_CONFIG

def test_rule_engineer_agent():
    """测试规则工程师智能体。"""
    print("初始化RuleEngineerAgent...")
    rule_engineer = RuleEngineerAgent(LLM_CONFIG)
    
    # 测试用例
    test_cases = [
        {
            "description": "Python中通过字符串连接进行SQL注入",
            "code": """query = "SELECT * FROM users WHERE username = '" + username + "'"""
        },
        {
            "description": "使用过时的MD5哈希函数",
            "code": """import hashlib\nhash = hashlib.md5(password.encode()).hexdigest()"""
        },
        {
            "description": "JavaScript中通过innerHTML的潜在XSS漏洞",
            "code": """document.getElementById("content").innerHTML = userInput;"""
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"测试 {i+1}: {test_case['description']}")
        print(f"{'='*60}")
        
        result = rule_engineer.create_or_update_rule(
            problem_description=test_case['description'],
            code_example=test_case['code']
        )
        
        if result['success']:
            print("✓ 规则创建成功!")
            print("\n规则内容:")
            print(result['rule_yaml'])
            
            # 保存规则到文件
            filename = f"test_rule_{i+1}.yaml"
            filepath = rule_engineer.save_rule_to_file(result['rule_yaml'], filename)
            print(f"\n规则保存位置: {filepath}")
        else:
            print("✗ 创建规则时出错:")
            print(result['message'])

def test_rule_update():
    """测试更新现有规则。"""
    print("\n\n" + "="*60)
    print("规则更新测试")
    print("="*60)
    
    rule_engineer = RuleEngineerAgent(LLM_CONFIG)
    
    # 类似规则的示例（模拟搜索结果）
    similar_rules = [
        {
            "id": "hardcoded-password",
            "message": "检测到硬编码密码",
            "source_file": "security_rules.yaml"
        }
    ]
    
    result = rule_engineer.create_or_update_rule(
        problem_description="检测Python代码中硬编码的密钥",
        code_example="""api_key = 'sk_1234567890abcdef'""",
        similar_rules=similar_rules
    )
    
    if result['success']:
        print("✓ 规则更新成功!")
        print("\n规则内容:")
        print(result['rule_yaml'])
        print(f"这是新规则: {result['is_new']}")
    else:
        print("✗ 更新规则时出错:")
        print(result['message'])

if __name__ == "__main__":
    test_rule_engineer_agent()
    test_rule_update()