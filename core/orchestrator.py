import autogen
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import os

from agents.search_agent import SearchAgent
from agents.rule_engineer_agent import RuleEngineerAgent
from agents.validation_agent import ValidationAgent
from utils.vector_db_manager import VectorDBManager
from config.llm_config import LLM_CONFIG

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Orchestrator:
    """
    主协调器，管理所有智能体和工作流程。
    """
    
    def __init__(self):
        """初始化系统的所有组件。"""
        self.llm_config = LLM_CONFIG
        
        # 初始化向量数据库管理器
        self.vector_db_manager = VectorDBManager()
        
        # 初始化智能体
        self.search_agent = SearchAgent(self.llm_config, self.vector_db_manager)
        self.rule_engineer_agent = RuleEngineerAgent(self.llm_config)
        self.validation_agent = ValidationAgent(self.llm_config)
        
        # 创建UserProxyAgent用于管理对话
        self.user_proxy = autogen.UserProxyAgent(
            name="User_Proxy",
            human_input_mode="NEVER",
            code_execution_config={"work_dir": "coding", "use_docker": False},
            max_consecutive_auto_reply=10,
        )
        
        logger.info("Orchestrator initialized all agents")

    def create_positive_test_case(self, code_snippet: str, vulnerability_description: str) -> str:
        """
        基于代码和漏洞描述创建正向测试用例。
        
        Args:
            code_snippet: 包含漏洞的源代码
            vulnerability_description: 漏洞描述
            
        Returns:
            准备好的测试用例
        """
        # 在真实系统中这里可能有更复杂的逻辑
        # 为简单起见，我们直接返回源代码
        return code_snippet

    def create_negative_test_case(self, code_snippet: str, vulnerability_description: str) -> str:
        """
        创建负向测试用例（无漏洞的代码）。
        
        Args:
            code_snippet: 包含漏洞的源代码
            vulnerability_description: 漏洞描述
            
        Returns:
            准备好的无漏洞测试用例
        """
        # 在真实系统中这里可能生成"干净"的代码
        # 或使用模板。为简单起见，我们返回简化版本
        if "sql" in vulnerability_description.lower():
            return "query = \"SELECT * FROM users WHERE status = 'active'\""
        elif "xss" in vulnerability_description.lower():
            return "element.textContent = userInput"
        else:
            return "# 无漏洞的干净代码\nresult = safe_function()"

    def run_full_workflow(self, code_snippet: str, vulnerability_description: str) -> Dict[str, Any]:
        """
        启动完整的请求处理工作流程。
        
        Args:
            code_snippet: 包含漏洞的代码
            vulnerability_description: 漏洞描述
            
        Returns:
            包含工作流程结果的字典
        """
        logger.info(f"Starting full workflow: {vulnerability_description}")
        
        # 步骤1: 搜索现有规则
        logger.info("Step 1: Searching existing rules...")
        search_result = self.search_agent.find_relevant_rules(vulnerability_description)
        
        # 提取找到的规则信息
        similar_rules = []
        if "Found the following relevant rules" in search_result:
            # 解析搜索结果以传递给工程师智能体
            lines = search_result.split("\n")
            for line in lines:
                if line.strip().startswith("ID:"):
                    rule_id = line.split("ID:")[1].split("\n")[0].strip()
                    similar_rules.append({"id": rule_id})
        
        # 步骤2: 创建或更新规则
        logger.info("Step 2: Creating/updating rules...")
        rule_result = self.rule_engineer_agent.create_or_update_rule(
            problem_description=vulnerability_description,
            code_example=code_snippet,
            similar_rules=similar_rules if similar_rules else None
        )
        
        if not rule_result["success"]:
            return {
                "success": False,
                "error": rule_result["message"],
                "step": "rule_creation"
            }
        
        # 步骤3: 准备测试用例
        logger.info("Step 3: Preparing test cases...")
        positive_test = self.create_positive_test_case(code_snippet, vulnerability_description)
        negative_test = self.create_negative_test_case(code_snippet, vulnerability_description)
        
        # 步骤4: 验证规则
        logger.info("Step 4: Validating rules...")
        validation_result = self.validation_agent.validate_rule(
            rule_yaml=rule_result["rule_yaml"],
            positive_test=positive_test,
            negative_test=negative_test,
            rule_id=rule_result.get("rule_id", "new_rule")
        )
        
        if not validation_result["success"]:
            return {
                "success": False,
                "error": validation_result.get("error", "Validation error"),
                "step": "validation",
                "rule_yaml": rule_result["rule_yaml"]  # 仍然返回规则
            }
        
        # 步骤5: 保存成功的规则
        logger.info("Step 5: Saving rules...")
        if validation_result.get("validation_passed", False):
            # 从YAML中提取规则ID作为文件名
            try:
                import yaml
                rule_data = yaml.safe_load(rule_result["rule_yaml"])
                rule_id = rule_data["rules"][0]["id"] if rule_data and "rules" in rule_data else "new_rule"
                filename = f"{rule_id}.yaml"
            except:
                filename = None
                
            saved_path = self.rule_engineer_agent.save_rule_to_file(
                rule_result["rule_yaml"], filename
            )
        else:
            saved_path = None
        
        # 形成最终结果
        result = {
            "success": True,
            "search_result": search_result,
            "rule_creation_success": rule_result["success"],
            "validation_passed": validation_result.get("validation_passed", False),
            "rule_yaml": rule_result["rule_yaml"],
            "validation_report": validation_result.get("llm_analysis", ""),
            "saved_path": saved_path,
            "is_new_rule": rule_result.get("is_new", True)
        }
        
        logger.info("Workflow completed successfully!")
        return result

    def run_interactive_workflow(self):
        """
        启动与用户的交互式工作模式。
        """
        print("=" * 60)
        print("用于创建SEMGREP规则的多智能体系统")
        print("=" * 60)
        
        while True:
            print("\n请输入漏洞描述 (或输入 'quit' 退出):")
            description = input().strip()
            
            if description.lower() == 'quit':
                break
                
            print("\n请输入包含漏洞的代码 (以空行结束):")
            code_lines = []
            while True:
                line = input()
                if line.strip() == "":
                    break
                code_lines.append(line)
            
            code_snippet = "\n".join(code_lines)
            
            if not code_snippet:
                print("代码不能为空!")
                continue
                
            print("\n处理请求...")
            result = self.run_full_workflow(code_snippet, description)
            
            print("\n" + "=" * 40)
            print("处理结果")
            print("=" * 40)
            
            if result["success"]:
                print("✓ 工作流程成功完成!")
                print(f"\n搜索: 找到 {result['search_result'].count('ID:')} 个相关规则")
                print(f"创建规则: {'成功' if result['rule_creation_success'] else '失败'}")
                print(f"验证: {'通过' if result['validation_passed'] else '未通过'}")
                print(f"类型: {'新规则' if result['is_new_rule'] else '规则更新'}")
                
                if result["saved_path"]:
                    print(f"保存位置: {result['saved_path']}")
                    
                print("\n验证报告:")
                print(result["validation_report"])
                
                print("\n规则内容:")
                print(result["rule_yaml"])
            else:
                print("✗ 工作流程以错误结束:")
                print(f"阶段: {result.get('step', 'unknown')}")
                print(f"错误: {result.get('error', '未知错误')}")
                
                if "rule_yaml" in result:
                    print("\n部分创建的规则:")
                    print(result["rule_yaml"])
            
            print("\n" + "=" * 40)

def main():
    """启动协调器的主函数。"""
    orchestrator = Orchestrator()
    orchestrator.run_interactive_workflow()


if __name__ == "__main__":
    main()