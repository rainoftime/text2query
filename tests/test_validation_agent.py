#!/usr/bin/env python3
"""
测试验证智能体。
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.validation_agent import ValidationAgent
from config.llm_config import LLM_CONFIG

def test_validation_agent():
    """测试验证智能体。"""
    print("初始化ValidationAgent...")
    validation_agent = ValidationAgent(LLM_CONFIG)
    
    # SQL注入的正确规则示例
    good_rule_yaml = """
rules:
- id: sql-injection-concat
  message: "Potential SQL injection through string concatenation"
  languages: [python]
  severity: ERROR
  patterns:
  - pattern: |
      $QUERY = "SELECT ... " + $USER_INPUT + " ..."
  - metavariable-regex:
      metavariable: $USER_INPUT
      regex: .*
"""

    # 错误规则示例（有语法错误）
    bad_rule_yaml = """
rules:
- id: bad-rule
  message: "This rule has syntax error"
  languages: [python]
  severity: ERROR
  pattern: |
    broken pattern without proper closure
"""

    # 测试代码示例
    positive_test = '''
query = "SELECT * FROM users WHERE username = '" + username + "'"
result = cursor.execute(query)
'''

    negative_test = '''
query = "SELECT * FROM users WHERE status = 'active'"
result = cursor.execute(query)
'''

    print("=" * 60)
    print("测试 1: 验证好的规则")
    print("=" * 60)
    
    result = validation_agent.validate_rule(
        rule_yaml=good_rule_yaml,
        positive_test=positive_test,
        negative_test=negative_test,
        rule_id="sql-injection-concat"
    )
    
    if result["success"]:
        print("✓ 验证成功完成!")
        print("\nLLM分析:")
        print(result["llm_analysis"])
        
        print("\n自动验证:")
        print(f"通过: {result['validation_passed']}")
        print(f"正向测试: {result['auto_validation']['positive_test']['success']}")
        print(f"负向测试: {result['auto_validation']['negative_test']['success']}")
    else:
        print("✗ 验证时出错:")
        print(result.get("error", "未知错误"))
    
    print("\n" + "=" * 60)
    print("测试 2: 验证坏的规则")
    print("=" * 60)
    
    result = validation_agent.validate_rule(
        rule_yaml=bad_rule_yaml,
        positive_test=positive_test,
        negative_test=negative_test,
        rule_id="bad-rule"
    )
    
    if result["success"]:
        print("✓ 验证完成 (预期失败)!")
        print("\nLLM分析:")
        print(result["llm_analysis"])
        
        print("\n自动验证:")
        print(f"通过: {result['validation_passed']}")
    else:
        print("✗ 验证时出错 (对坏规则是预期的):")
        print(result.get("error", "未知错误"))

if __name__ == "__main__":
    test_validation_agent()