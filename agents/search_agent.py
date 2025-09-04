import autogen
from typing import Optional, Dict, Any
import logging
from utils.prompts import SEARCH_AGENT_SYSTEM_MESSAGE

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchAgent:
    """
    基于漏洞描述在向量数据库中搜索相关规则的智能体。
    """
    
    def __init__(self, llm_config: Dict[str, Any], vector_db_manager):
        """
        初始化搜索智能体。
        
        Args:
            llm_config: AutoGen的LLM配置
            vector_db_manager: 用于访问向量数据库的VectorDBManager实例
        """
        self.llm_config = llm_config
        self.vector_db_manager = vector_db_manager
        
        # 创建AutoGen智能体
        self.agent = autogen.AssistantAgent(
            name="Search_Agent",
            system_message=SEARCH_AGENT_SYSTEM_MESSAGE,
            llm_config=self.llm_config,
        )
        
        # 注册搜索函数供智能体使用
        self.register_functions()
        logger.info("Search agent initialized")

    def register_functions(self):
        """注册智能体可以调用的函数。"""
        
        @self.agent.register_for_llm(description="Search for relevant rules in database based on text query")
        def query_rules(query_text: str, n_results: int = 5) -> str:
            """
            根据文本查询在数据库中搜索相关规则。
            
            Args:
                query_text: 用于搜索的查询文本
                n_results: 返回结果的数量
                
            Returns:
                包含搜索结果的字符串
            """
            try:
                results = self.vector_db_manager.query_rules(query_text, n_results)
                
                if not results:
                    return "No rules found based on your query."
                
                # 将结果格式化为可读形式
                formatted_results = []
                for i, result in enumerate(results):
                    formatted_results.append(
                        f"{i+1}. ID: {result['id']}\n"
                        f"   Message: {result['metadata']['message']}\n"
                        f"   Severity: {result['metadata']['severity']}\n"
                        f"   Source: {result['metadata']['source_file']}\n"
                        f"   Similarity: {result['distance']:.4f}\n"
                    )
                
                return "Found the following relevant rules:\n\n" + "\n".join(formatted_results)
                
            except Exception as e:
                error_msg = f"Error during search execution: {str(e)}"
                logger.error(error_msg)
                return error_msg

    def formulate_search_query(self, problem_description: str) -> str:
        """
        根据问题描述制定搜索查询。
        
        Args:
            problem_description: 漏洞或问题的描述
            
        Returns:
            制定的搜索查询
        """
        try:
            # 创建UserProxyAgent与Search Agent交互
            user_proxy = autogen.UserProxyAgent(
                name="User_Proxy",
                human_input_mode="NEVER",
                code_execution_config={"work_dir": "coding", "use_docker": False},
                max_consecutive_auto_reply=1,
            )
            
            # 启动对话以制定搜索查询
            user_proxy.initiate_chat(
                self.agent,
                message=f"""
                Analyze the following vulnerability description and formulate a precise search query for the rule database:
                
                {problem_description}
                
                Return only the search query, no additional comments.
                """,
            )
            
            # 获取智能体的最后回复
            last_message = self.agent.last_message()
            if last_message and "content" in last_message:
                return last_message["content"].strip()
            else:
                logger.warning("Agent did not return search query")
                return problem_description  # 备用方案 - 使用原始描述
                
        except Exception as e:
            logger.error(f"Error during search query formulation: {str(e)}")
            return problem_description  # 备用方案 - 使用原始描述

    def find_relevant_rules(self, problem_description: str, n_results: int = 5) -> str:
        """
        搜索相关规则的主要方法。
        
        Args:
            problem_description: 漏洞或问题的描述
            n_results: 返回结果的数量
            
        Returns:
            包含搜索结果的字符串
        """
        # 首先制定最优的搜索查询
        search_query = self.formulate_search_query(problem_description)
        logger.info(f"Search query formulated: '{search_query}'")
        
        # 然后在向量数据库中执行搜索
        try:
            results = self.vector_db_manager.query_rules(search_query, n_results)
            
            if not results:
                return "No rules found based on your query."
            
            # 将结果格式化为可读形式
            formatted_results = []
            for i, result in enumerate(results):
                formatted_results.append(
                    f"{i+1}. ID: {result['id']}\n"
                    f"   Message: {result['metadata']['message']}\n"
                    f"   Severity: {result['metadata']['severity']}\n"
                    f"   Source: {result['metadata']['source_file']}\n"
                    f"   Similarity: {result['distance']:.4f}\n"
                )
            
            return "Found the following relevant rules:\n\n" + "\n".join(formatted_results)
            
        except Exception as e:
            error_msg = f"Error during search execution: {str(e)}"
            logger.error(error_msg)
            return error_msg