# 多语言支持功能测试

本目录包含MetaGPT多语言支持功能的测试文件。

## 测试文件说明

### 1. `test_simple_multilingual.py`
**简化功能测试**
- 测试基本语言检测功能（不使用LLM）
- 测试提示词渲染功能
- 测试语言上下文管理
- 适合快速验证核心功能

**运行方式：**
```bash
cd tests/multilingual
python test_simple_multilingual.py
```

### 2. `test_multilingual_support.py`
**完整功能测试**
- 测试所有语言检测方法（包括LLM检测）
- 测试SLC工具的多语言支持
- 测试完整集成流程
- 适合全面验证所有功能

**运行方式：**
```bash
cd tests/multilingual
python test_multilingual_support.py
```

## 测试环境要求

1. **Python环境**：Python 3.8+
2. **MetaGPT**：已安装并配置
3. **Ollama**：本地Ollama服务运行中
4. **配置文件**：`config/config2.yaml` 已正确配置

## 测试覆盖范围

### 语言检测测试
- ✅ 中文检测
- ✅ 英文检测
- ✅ 韩文检测
- ✅ 日文检测
- ✅ 西班牙文检测
- ✅ 法文检测
- ✅ 其他语言检测

### 提示词渲染测试
- ✅ 基本提示词渲染
- ✅ 带变量提示词渲染
- ✅ 多语言环境测试

### 上下文管理测试
- ✅ 语言自动检测
- ✅ 强制语言设置
- ✅ 语言重置功能
- ✅ 置信度评估

### 集成测试
- ✅ Action基类集成
- ✅ Role基类集成
- ✅ SLC工具集成

## 测试结果解读

### 成功指标
- 语言检测准确率 > 90%
- 提示词渲染正确
- 上下文管理功能完整
- 无异常错误

### 常见问题
1. **LLM检测失败**：检查Ollama服务状态和配置
2. **API调用错误**：检查网络连接和API密钥
3. **导入错误**：检查Python路径和依赖安装

## 持续集成

建议在CI/CD流程中包含这些测试：
```yaml
# .github/workflows/multilingual-test.yml
- name: Test Multilingual Support
  run: |
    cd tests/multilingual
    python test_simple_multilingual.py
    python test_multilingual_support.py
```

## 贡献指南

添加新测试时请遵循以下规范：
1. 测试文件命名：`test_*.py`
2. 测试函数命名：`test_*`
3. 添加适当的文档说明
4. 确保测试的可重复性 