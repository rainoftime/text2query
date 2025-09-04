"""
AutoGen的LLM配置。
"""

LLM_CONFIG = {
    "config_list": [
        {
            "model": "deepseek-coder:6.7b",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
        }
    ],
    "temperature": 0.1,
    "timeout": 120,
    "cache_seed": 42  # 用于结果的可重现性
}

# 工程师智能体的配置（更高的温度用于创造性）
RULE_ENGINEER_LLM_CONFIG = {
    "config_list": LLM_CONFIG["config_list"],
    "temperature": 0.3,  # 更高的温度用于创造性
    "timeout": 180,      # 更多时间用于生成复杂规则
    "cache_seed": 42
}