
# 一些思考


- semgrep规则来源
- Positive / Negative Example 的来源
- 检索优化

## Semgrep规则来源

- semgrep官方规则库：本项目默认使用的（带下载脚本）
- https://github.com/trailofbits/semgrep-rules
- ...

其他可能性：可以用CodeQL、Clang tidy等分析器的规则自动”翻译“吗？

## Positive / Negative Example 的来源

### 1. 来自官方规则库的测试集

Semgrep 官方规则库里，很多规则都有配套的 test cases（通常在 `tests/` 目录下，包含触发漏洞的代码和正常代码）。

这些天然可以作为：

- **Positive examples** = 应该触发告警的漏洞代码
- **Negative examples** = 不该触发的安全代码

**优点：** 有专家维护，质量较高

**缺点：** 覆盖度有限，有些规则没有完善的测试

### 2. 来自历史提交 / commit log

RuleRefiner 的论文里就是这么做的：从 Semgrep 的 GitHub repo 历史 commit 中，挖掘修复某条规则时附带的测试用例。

每次规则被修改 → 通常会新增一两个 defect-revealing case（可能是 false positive 或 false negative）。

同时，原有的 regression tests 可以作为正反例的补充。

**优点：** 完全真实的"误报/漏报"场景

**缺点：** 挖掘过程需要自动化脚本+人工清洗

### 3. 来自自动生成 (Fuzzing / Program Transformations)

你可以用工具自动变异已有测试用例：

- **Metamorphic Testing：** 在保持语义等价的情况下修改代码（改变量名、换同义 API、增加无关代码），生成更多 negative / positive 变体
- **FuzzSlice / Statfier**（论文里提到过）可以生成大量"语义保持变体"，帮助扩大训练/验证集

这样，你能在有限人工测试的基础上，自动扩充出一堆正反例。

### 4. 来自真实项目扫描

运行 Semgrep 官方规则，在真实项目（比如 GitHub 开源代码库）上收集告警。

然后通过：

- 人工标注
- 已有漏洞数据库对齐（如 CVE、Snyk DB）
- 交叉工具验证（不同 static analyzer 一致认为的 → 正例，不一致的 → 可疑）

这些结果也可以作为 positive/negative 的来源。

**缺点：** 需要大量人工或额外 oracle

## 检索优化

### 1. 多模型嵌入策略

- 使用 `microsoft/codebert-base` 等专门针对代码语义
- 添加 `paraphrase-multilingual-MiniLM-L12-v2` 支持多语言
- 更好的代码模式理解能力

### 2. 多维度文本表示

- **语义表示：** 用于概念匹配
- **模式表示：** 用于代码模式匹配
- **漏洞表示：** 用于漏洞类型匹配

### 3. 混合检索策略

- 结合多种检索方法
- 结果合并和去重
- 智能排序优化