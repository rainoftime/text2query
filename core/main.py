#!/usr/bin/env python3
"""
应用程序的主入口点。
运行: python main.py
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.orchestrator import main

if __name__ == "__main__":
    main()