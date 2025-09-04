import autogen
import yaml
import re
from typing import Dict, Any, Optional, List
import logging
from utils.prompts import RULE_ENGINEER_AGENT_SYSTEM_MESSAGE
from config.llm_config import RULE_ENGINEER_LLM_CONFIG

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuleEngineerAgent:
    """
    用于创建和修改Semgrep规则的智能体。
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化规则工程师智能体。
        
        Args:
            llm_config: AutoGen的LLM配置
        """
        self.llm_config = llm_config or RULE_ENGINEER_LLM_CONFIG
        
        # 创建AutoGen智能体
        self.agent = autogen.AssistantAgent(
            name="Rule_Engineer_Agent",
            system_message=RULE_ENGINEER_AGENT_SYSTEM_MESSAGE,
            llm_config=self.llm_config,
        )
        
        logger.info("Rule engineer agent initialized")

    def extract_yaml_from_response(self, response: str) -> Optional[str]:
        """
        从代理响应中提取YAML块。
        
        Args:
            response: 可能包含YAML块的代理响应
            
        Returns:
            提取的YAML或None（如果未找到）
        """
        # 在```yaml和```之间查找YAML块
        yaml_pattern = r"```yaml\s*(.*?)\s*```"
        match = re.search(yaml_pattern, response, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # 如果没有找到带yaml标记的，尝试查找任何代码块
        code_pattern = r"```\s*(.*?)\s*```"
        match = re.search(code_pattern, response, re.DOTALL)
        
        if match:
            # 检查内容是否看起来像YAML
            content = match.group(1).strip()
            if content.startswith("rules:") or "id:" in content and "message:" in content:
                return content
        
        logger.warning("Unable to extract YAML from agent response")
        return None

    def validate_yaml(self, yaml_content: str) -> bool:
        """
        验证YAML内容的有效性。
        
        Args:
            yaml_content: 要验证的YAML字符串
            
        Returns:
            如果YAML有效返回True，否则返回False
        """
        try:
            yaml.safe_load(yaml_content)
            return True
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML: {str(e)}")
            return False

    def create_or_update_rule(self, problem_description: str, code_example: str = None, 
                             similar_rules: List[Dict] = None) -> Dict[str, Any]:
        """
        基于问题描述创建新规则或更新现有规则。
        
        Args:
            problem_description: 漏洞描述
            code_example: 包含漏洞的代码示例（可选）
            similar_rules: 相似规则列表（可选）
            
        Returns:
            包含结果的字典：{
                'success': bool,
                'rule_yaml': str,  # 规则的YAML内容
                'message': str,    # 错误或成功消息
                'is_new': bool     # 如果是新规则为True，如果是更新为False
            }
        """
        try:
            # 创建UserProxyAgent与代理交互
            user_proxy = autogen.UserProxyAgent(
                name="User_Proxy",
                human_input_mode="NEVER",
                code_execution_config={"work_dir": "coding", "use_docker": False},
                max_consecutive_auto_reply=2,
            )
            
            # 为代理构建消息
            message = f"""
            Need to create or update Semgrep rule to detect the following vulnerability:
            
            Description: {problem_description}
            """
            
            if code_example:
                message += f"""
                
            Code example with vulnerability:
            ```python
            {code_example}
            ```
            """
            
            if similar_rules:
                message += "\n\nSimilar rules in database:\n"
                for i, rule in enumerate(similar_rules):
                    message += f"\n{i+1}. ID: {rule.get('id', 'N/A')}\n"
                    message += f"   Message: {rule.get('message', 'N/A')}\n"
                    message += f"   Source: {rule.get('source_file', 'N/A')}\n"
            
            message += "\nPlease create a new rule or modify the most suitable similar rule."
            
            # 启动对话
            user_proxy.initiate_chat(
                self.agent,
                message=message,
            )
            
            # 获取代理响应
            last_message = self.agent.last_message()
            if last_message and "content" in last_message:
                response_content = last_message["content"]
                
                # 从响应中提取YAML
                yaml_content = self.extract_yaml_from_response(response_content)
                
                if yaml_content and self.validate_yaml(yaml_content):
                    # 确定这是新规则还是更新
                    is_new = similar_rules is None or len(similar_rules) == 0
                    
                    return {
                        'success': True,
                        'rule_yaml': yaml_content,
                        'message': "Rule successfully created/updated",
                        'is_new': is_new
                    }
                else:
                    return {
                        'success': False,
                        'rule_yaml': None,
                        'message': "Unable to extract valid YAML from agent response",
                        'is_new': False
                    }
            else:
                return {
                    'success': False,
                    'rule_yaml': None,
                    'message': "Agent did not return response",
                    'is_new': False
                }
                
        except Exception as e:
            error_msg = f"Error during rule creation/update: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'rule_yaml': None,
                'message': error_msg,
                'is_new': False
            }

    def save_rule_to_file(self, yaml_content: str, filename: str = None) -> str:
        """
        将规则保存到YAML文件。
        
        Args:
            yaml_content: 规则的YAML内容
            filename: 文件名（可选）
            
        Returns:
            保存文件的路径
        """
        import os
        from datetime import datetime
        
        # 如果不存在，创建规则目录
        rules_dir = "./data/generated_rules"
        os.makedirs(rules_dir, exist_ok=True)
        
        # 如果未提供，生成文件名
        if filename is None:
            # 尝试从YAML中提取规则ID
            rule_data = yaml.safe_load(yaml_content)
            if rule_data and 'rules' in rule_data and len(rule_data['rules']) > 0:
                rule_id = rule_data['rules'][0].get('id', 'unknown')
                filename = f"{rule_id}.yaml"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"new_rule_{timestamp}.yaml"
        
        filepath = os.path.join(rules_dir, filename)
        
        # 将规则保存到文件
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(yaml_content)
        
        logger.info(f"Rule saved to file: {filepath}")
        return filepath