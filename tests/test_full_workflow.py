#!/usr/bin/env python3
"""
测试系统的完整工作流程。
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.orchestrator import Orchestrator

def test_full_workflow():
    """测试完整的工作流程。"""
    print("初始化协调器...")
    orchestrator = Orchestrator()
    
    # 测试用例
    test_cases = [
        {
            "description": "Python中通过字符串连接进行SQL注入",
            "code": """
query = "SELECT * FROM users WHERE username = '" + username + "'"
result = cursor.execute(query)
"""
        },
        {
            "description": "使用过时的MD5哈希函数",
            "code": """
import hashlib
hash = hashlib.md5(password.encode()).hexdigest()
"""
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'=' * 60}")
        print(f"测试 {i+1}: {test_case['description']}")
        print(f"{'=' * 60}")
        
        result = orchestrator.run_full_workflow(
            code_snippet=test_case["code"],
            vulnerability_description=test_case["description"]
        )
        
        if result["success"]:
            print("✓ 工作流程成功完成!")
            print(f"创建规则: {'成功' if result['rule_creation_success'] else '失败'}")
            print(f"验证: {'通过' if result['validation_passed'] else '未通过'}")
            print(f"类型: {'新规则' if result['is_new_rule'] else '规则更新'}")
            
            if result["saved_path"]:
                print(f"保存位置: {result['saved_path']}")
        else:
            print("✗ 工作流程以错误结束:")
            print(f"阶段: {result.get('step', 'unknown')}")
            print(f"错误: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    test_full_workflow()