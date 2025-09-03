#!/usr/bin/env python3
"""
从官方Semgrep仓库更新规则的脚本。
运行: python scripts/update_rules.py
"""

import os
import subprocess
import shutil
from utils.vector_db_manager import VectorDBManager

def update_rules():
    """从官方Semgrep仓库更新规则。"""
    print("从官方仓库更新规则...")
    
    # 目录路径
    official_dir = "./data/official_rules"
    raw_dir = "./data/raw_rules"
    backup_dir = "./data/backup_rules"
    
    # 创建当前规则的备份
    if os.path.exists(raw_dir):
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(raw_dir, backup_dir)
        print(f"在 {backup_dir} 创建了规则备份")
    
    # 更新仓库
    if os.path.exists(official_dir):
        os.chdir(official_dir)
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        if result.returncode == 0:
            print("仓库更新成功")
        else:
            print(f"更新仓库时出错: {result.stderr}")
        os.chdir("../..")
    else:
        # 如果仓库不存在则克隆
        result = subprocess.run([
            "git", "clone", 
            "https://github.com/semgrep/semgrep-rules.git", 
            official_dir
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("仓库克隆成功")
        else:
            print(f"克隆仓库时出错: {result.stderr}")
            return False
    
    # 将规则复制到工作目录
    if os.path.exists(raw_dir):
        shutil.rmtree(raw_dir)
    shutil.copytree(official_dir, raw_dir)
    
    # 删除git服务文件
    git_dir = os.path.join(raw_dir, ".git")
    if os.path.exists(git_dir):
        shutil.rmtree(git_dir)
    
    # 删除README和其他不需要的文件
    for file in ["README.md", "LICENSE", ".gitignore"]:
        file_path = os.path.join(raw_dir, file)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    print("规则更新成功")
    
    # 重建向量数据库
    print("重建向量数据库...")
    db_manager = VectorDBManager()
    db_manager.build_vector_db(raw_dir)
    
    return True

if __name__ == "__main__":
    update_rules()