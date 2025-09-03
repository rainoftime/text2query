#!/usr/bin/env python3
"""
用于从Semgrep规则构建向量数据库的脚本。
现在支持官方仓库的结构。
"""

import sys
import os
import yaml

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.vector_db_manager import VectorDBManager

def build_vector_db_from_rules(rules_dir: str = "./data/raw_rules"):
    """
    用于从规则快速构建向量数据库的实用函数。
    现在递归处理子目录。
    
    Args:
        rules_dir (str): Semgrep规则目录的路径
    """
    db_manager = VectorDBManager()
    
    # 递归扫描所有子目录
    yaml_files = []
    for root, dirs, files in os.walk(rules_dir):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                yaml_files.append(os.path.join(root, file))
    
    print(f"在 {rules_dir} 中找到 {len(yaml_files)} 个YAML文件")
    db_manager.build_vector_db(rules_dir)


if __name__ == "__main__":
    print("开始构建Semgrep规则的向量数据库...")
    build_vector_db_from_rules()
    print("向量数据库构建成功!")