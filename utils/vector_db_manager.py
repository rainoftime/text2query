import os
import yaml
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDBManager:
    """
    用于管理Semgrep规则向量数据库的类。
    负责创建、填充和查询向量数据库。
    """
    
    def __init__(self, persist_directory: str = "./data/vector_db"):
        self.persist_directory = persist_directory
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 初始化ChromaDB客户端
        self.chroma_client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                is_persistent=True,
            )
        )
        
        # 创建或获取集合
        self.collection = self.chroma_client.get_or_create_collection(
            name="semgrep_rules",
            metadata={"hnsw:space": "cosine"} # 使用余弦距离进行相似性计算
        )
        logger.info("向量数据库管理器已初始化")

    def load_and_process_rules(self, rules_directory: str) -> List[Dict[str, Any]]:
        """
        加载并处理指定目录中的所有YAML规则文件。
        递归处理子目录。
        """
        processed_rules = []
        
        if not os.path.exists(rules_directory):
            raise FileNotFoundError(f"规则目录未找到: {rules_directory}")
        
        # 递归搜索所有YAML文件
        yaml_files = []
        for root, dirs, files in os.walk(rules_directory):
            for filename in files:
                if filename.endswith(('.yaml', '.yml')):
                    yaml_files.append(os.path.join(root, filename))
        
        for filepath in yaml_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    rule_data = yaml.safe_load(file)
                    
                    # 跳过没有规则的文件
                    if not rule_data or 'rules' not in rule_data:
                        continue
                    
                    # 提取文件中每个规则的信息
                    for rule in rule_data.get('rules', []):
                        rule_id = rule.get('id', '')
                        rule_message = rule.get('message', '')
                        rule_severity = rule.get('severity', '')
                        rule_languages = rule.get('languages', [])
                        
                        # 提取元数据以改善搜索
                        metadata = rule.get('metadata', {})
                        rule_category = metadata.get('category', '')
                        rule_technology = metadata.get('technology', [])
                        rule_cwe = metadata.get('cwe', [])
                        
                        # 创建用于嵌入的合并文本
                        combined_text = f"""
                        ID: {rule_id}
                        Message: {rule_message}
                        Severity: {rule_severity}
                        Languages: {rule_languages}
                        Category: {rule_category}
                        Technology: {rule_technology}
                        CWE: {rule_cwe}
                        """
                        
                        processed_rules.append({
                            'id': rule_id,
                            'message': rule_message,
                            'severity': rule_severity,
                            'languages': rule_languages,
                            'category': rule_category,
                            'technology': rule_technology,
                            'cwe': rule_cwe,
                            'combined_text': combined_text,
                            'source_file': os.path.relpath(filepath, rules_directory)
                        })
                        
            except Exception as e:
                logger.error(f"处理文件时出错 {filepath}: {str(e)}")
                continue
        
        logger.info(f"成功处理了 {len(processed_rules)} 个规则，来自 {len(yaml_files)} 个文件")
        return processed_rules

    def build_vector_db(self, rules_directory: str):
        """
        从规则构建向量数据库的主要方法。
        
        Args:
            rules_directory (str): Semgrep规则目录的路径
        """
        # 加载和处理规则
        rules = self.load_and_process_rules(rules_directory)
        
        if not rules:
            logger.warning("未找到要处理的规则。向量数据库将不会被创建。")
            return
        
        # 准备要添加到集合的数据
        ids = []
        documents = []
        metadatas = []
        
        for rule in rules:
            ids.append(rule['id'])
            documents.append(rule['combined_text'])
            metadatas.append({
                'source_file': rule['source_file'],
                'severity': rule['severity'],
                'languages': str(rule['languages']),
                'message': rule['message']
            })
        
        # 生成嵌入
        logger.info("为规则生成嵌入...")
        embeddings = self.embedder.encode(documents).tolist()
        
        # 将数据添加到集合
        logger.info("将数据添加到向量数据库...")
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # 将数据库保存到磁盘
        self.chroma_client.persist()
        logger.info(f"向量数据库成功构建并保存到 {self.persist_directory}")
        logger.info(f"添加了 {len(ids)} 个规则")

    def query_rules(self, query_text: str, n_results: int = 5) -> List[Dict]:
        """
        对规则向量数据库执行语义搜索。
        
        Args:
            query_text (str): 查询文本（漏洞描述）
            n_results (int): 返回结果的数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        # 为查询生成嵌入
        query_embedding = self.embedder.encode([query_text]).tolist()
        
        # 对集合执行查询
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        # 格式化结果
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'distance': results['distances'][0][i],
                'metadata': results['metadatas'][0][i],
                'document': results['documents'][0][i]
            })
        
        logger.info(f"为查询找到 {len(formatted_results)} 个结果: '{query_text}'")
        return formatted_results

# 用于简单使用类的函数
def build_vector_db_from_rules(rules_dir: str = "./data/raw_rules"):
    """
    用于从规则快速构建向量数据库的实用函数。
    
    Args:
        rules_dir (str): Semgrep规则目录的路径
    """
    db_manager = VectorDBManager()
    db_manager.build_vector_db(rules_dir)

if __name__ == "__main__":
    # 如果脚本直接运行，构建数据库
    build_vector_db_from_rules()