import autogen
from typing import Dict, Any, Optional
import logging
from utils.prompts import VALIDATION_AGENT_SYSTEM_MESSAGE
from utils.semgrep_runner import SemgrepRunner

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationAgent:
    """
    使用Semgrep CLI验证Semgrep规则的智能体。
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化验证智能体。
        
        Args:
            llm_config: AutoGen的LLM配置
        """
        self.llm_config = llm_config
        self.semgrep_runner = SemgrepRunner()
        
        # 创建AutoGen智能体
        self.agent = autogen.AssistantAgent(
            name="Validation_Agent",
            system_message=VALIDATION_AGENT_SYSTEM_MESSAGE,
            llm_config=self.llm_config,
        )
        
        # 注册验证函数供智能体使用
        self.register_functions()
        logger.info("Validation agent initialized")

    def register_functions(self):
        """注册智能体可以调用的函数。"""
        
        @self.agent.register_for_llm(description="Run Semgrep on test code to validate rules")
        def validate_rule_with_semgrep(rule_yaml: str, test_code: str, test_type: str = "positive") -> str:
            """
            使用Semgrep CLI执行规则验证。
            
            Args:
                rule_yaml: Semgrep规则的YAML内容
                test_code: 用于测试的代码
                test_type: 测试类型（"positive"或"negative"）
                
            Returns:
                包含Semgrep执行结果的字符串
            """
            try:
                result = self.semgrep_runner.run_semgrep(rule_yaml, test_code)
                
                if not result["success"]:
                    return f"Error executing Semgrep ({test_type} test): {result.get('error', 'Unknown error')}"
                
                if test_type == "positive":
                    expected = "vulnerability detected"
                    success = len(result["results"]) > 0
                else:  # negative
                    expected = "vulnerability not detected" 
                    success = len(result["results"]) == 0
                
                status = "Success" if success else "Failed"
                
                response = f"""
                ### {test_type.capitalize()} Test:
                - **Result:** {status} - Rule {'' if success else 'does not '}{expected}
                - **Trigger Count:** {len(result['results'])}
                - **Errors:** {len(result.get('errors', []))}
                """
                
                if result["results"]:
                    response += "\n- **Detected Triggers:**"
                    for i, match in enumerate(result["results"][:3]):  # 显示前3个
                        response += f"\n  {i+1}. {match.get('message', 'No message')}"
                
                if result.get("errors"):
                    response += "\n- **Semgrep Errors:**"
                    for error in result.get("errors", [])[:3]:  # 显示前3个错误
                        response += f"\n  - {error.get('message', 'Unknown error')}"
                
                return response
                
            except Exception as e:
                error_msg = f"Unexpected error during rule validation: {str(e)}"
                logger.error(error_msg)
                return error_msg

    def validate_rule(self, rule_yaml: str, positive_test: str, 
                     negative_test: str, rule_id: str = "unknown") -> Dict[str, Any]:
        """
        验证规则的主要方法。
        
        Args:
            rule_yaml: Semgrep规则的YAML内容
            positive_test: 包含漏洞的代码（应该被检测到）
            negative_test: 无漏洞的代码（不应该被检测到）
            rule_id: 规则ID用于报告
            
        Returns:
            包含验证结果的字典
        """
        try:
            # 创建UserProxyAgent用于与智能体交互
            user_proxy = autogen.UserProxyAgent(
                name="User_Proxy",
                human_input_mode="NEVER",
                code_execution_config={"work_dir": "coding", "use_docker": False},
                max_consecutive_auto_reply=2,
            )
            
            # 启动验证
            user_proxy.initiate_chat(
                self.agent,
                message=f"""
                Please test the following Semgrep rule and provide a detailed report:
                
                ## Rule (ID: {rule_id}):
                ```yaml
                {rule_yaml}
                ```
                
                ## Positive Test (code with vulnerability):
                ```python
                {positive_test}
                ```
                
                ## Negative Test (code without vulnerability):
                ```python
                {negative_test}
                ```
                
                Please test the rule on both examples and provide conclusions.
                """,
            )
            
            # 获取智能体的回复
            last_message = self.agent.last_message()
            if last_message and "content" in last_message:
                response_content = last_message["content"]
                
                # 同时运行自动验证以进行客观评估
                auto_validation = self.semgrep_runner.validate_rule(
                    rule_yaml, positive_test, negative_test
                )
                
                return {
                    "success": True,
                    "llm_analysis": response_content,
                    "auto_validation": auto_validation,
                    "validation_passed": auto_validation["validation_passed"]
                }
            else:
                return {
                    "success": False,
                    "error": "Agent did not return response",
                    "validation_passed": False
                }
                
        except Exception as e:
            error_msg = f"Error during rule validation: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "validation_passed": False
            }