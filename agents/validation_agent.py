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
        logger.info("验证智能体已初始化")

    def register_functions(self):
        """注册智能体可以调用的函数。"""
        
        @self.agent.register_for_llm(description="运行Semgrep在测试代码上验证规则")
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
                    return f"执行Semgrep时出错 ({test_type} 测试): {result.get('error', '未知错误')}"
                
                if test_type == "positive":
                    expected = "检测到漏洞"
                    success = len(result["results"]) > 0
                else:  # negative
                    expected = "不检测到漏洞"
                    success = len(result["results"]) == 0
                
                status = "成功" if success else "失败"
                
                response = f"""
                ### {test_type.capitalize()} 测试:
                - **结果:** {status} - 规则 {'' if success else '不'}{expected}
                - **触发次数:** {len(result['results'])}
                - **错误:** {len(result.get('errors', []))}
                """
                
                if result["results"]:
                    response += "\n- **检测到的触发:**"
                    for i, match in enumerate(result["results"][:3]):  # 显示前3个
                        response += f"\n  {i+1}. {match.get('message', '无消息')}"
                
                if result.get("errors"):
                    response += "\n- **Semgrep错误:**"
                    for error in result.get("errors", [])[:3]:  # 显示前3个错误
                        response += f"\n  - {error.get('message', '未知错误')}"
                
                return response
                
            except Exception as e:
                error_msg = f"验证规则时发生意外错误: {str(e)}"
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
                请测试以下Semgrep规则并提供详细报告:
                
                ## 规则 (ID: {rule_id}):
                ```yaml
                {rule_yaml}
                ```
                
                ## 正向测试（包含漏洞的代码）:
                ```python
                {positive_test}
                ```
                
                ## 负向测试（不含漏洞的代码）:
                ```python
                {negative_test}
                ```
                
                请在两个示例上测试规则并提供结论。
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
                    "error": "智能体未返回响应",
                    "validation_passed": False
                }
                
        except Exception as e:
            error_msg = f"验证规则时出错: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "validation_passed": False
            }