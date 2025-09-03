import subprocess
import tempfile
import os
import json
import logging
from typing import Dict, Any, List, Optional

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemgrepRunner:
    """
    用于运行Semgrep CLI和分析结果的类。
    """
    
    def __init__(self):
        """检查是否安装了Semgrep CLI。"""
        try:
            result = subprocess.run(["semgrep", "--version"], 
                                  capture_output=True, text=True, check=True)
            self.semgrep_available = True
            logger.info(f"Semgrep CLI可用: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.semgrep_available = False
            logger.error("Semgrep CLI未安装或不在PATH中")

    def run_semgrep(self, rule_content: str, test_code: str, 
                   language: str = "python") -> Dict[str, Any]:
        """
        运行Semgrep来检查测试代码上的规则。
        
        Args:
            rule_content: Semgrep规则的YAML内容
            test_code: 用于测试的代码
            language: 测试代码的编程语言
            
        Returns:
            包含Semgrep执行结果的字典
        """
        if not self.semgrep_available:
            return {
                "success": False,
                "error": "Semgrep CLI不可用",
                "results": []
            }
        
        try:
            # 为规则和测试代码创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as rule_file:
                rule_file.write(rule_content)
                rule_path = rule_file.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as code_file:
                code_file.write(test_code)
                code_path = code_file.name
            
            # 运行Semgrep
            cmd = [
                "semgrep", 
                "--config", rule_path,
                "--json",
                code_path
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30  # 30秒超时
            )
            
            # 删除临时文件
            os.unlink(rule_path)
            os.unlink(code_path)
            
            if result.returncode == 0:
                # 解析JSON输出
                output = json.loads(result.stdout)
                
                return {
                    "success": True,
                    "results": output.get("results", []),
                    "errors": output.get("errors", []),
                    "stats": output.get("stats", {})
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "results": [],
                    "errors": []
                }
                
        except subprocess.TimeoutExpired:
            logger.error("Semgrep执行超时")
            return {
                "success": False,
                "error": "执行超时",
                "results": []
            }
        except json.JSONDecodeError:
            logger.error("无法解析Semgrep的JSON输出")
            return {
                "success": False,
                "error": "无效的JSON输出",
                "results": []
            }
        except Exception as e:
            logger.error(f"执行Semgrep时发生意外错误: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }

    def validate_rule(self, rule_content: str, positive_test: str, 
                     negative_test: str, language: str = "python") -> Dict[str, Any]:
        """
        在正向和负向测试上完整验证规则。
        
        Args:
            rule_content: Semgrep规则的YAML内容
            positive_test: 包含漏洞的代码（应该被检测到）
            negative_test: 无漏洞的代码（不应该被检测到）
            language: 测试代码的编程语言
            
        Returns:
            包含验证结果的字典
        """
        # 在正向示例上测试
        positive_result = self.run_semgrep(rule_content, positive_test, language)
        
        # 在负向示例上测试
        negative_result = self.run_semgrep(rule_content, negative_test, language)
        
        # 分析结果
        validation_passed = (
            positive_result["success"] and 
            negative_result["success"] and
            len(positive_result["results"]) > 0 and  # 检测到漏洞
            len(negative_result["results"]) == 0     # 没有误报
        )
        
        return {
            "validation_passed": validation_passed,
            "positive_test": positive_result,
            "negative_test": negative_result,
            "details": {
                "positive_detected": len(positive_result["results"]) > 0,
                "negative_detected": len(negative_result["results"]) > 0,
                "errors": positive_result.get("errors", []) + negative_result.get("errors", [])
            }
        }