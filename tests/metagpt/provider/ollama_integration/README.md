# Ollama 集成测试

这个目录包含 MetaGPT 与 Ollama 集成的完整测试套件。

## 📁 目录结构

```
tests/metagpt/provider/ollama_integration/
├── __init__.py                    # 包初始化文件
├── README.md                      # 本文件
├── run_ollama_tests.py           # 测试运行脚本
├── test_ollama_basic.py          # 基础功能测试
├── test_ollama_api.py            # API 调用测试
└── test_ollama_integration.py    # 完整集成测试
```

## 🧪 测试文件说明

### 1. `test_ollama_basic.py` - 基础功能测试
- **功能**: 测试 Ollama 服务状态、模块导入、配置文件等基础功能
- **运行方式**: `python test_ollama_basic.py`
- **测试内容**:
  - Ollama 服务状态检查
  - API 模块导入测试
  - 配置文件加载测试
  - GPU 使用情况检查

### 2. `test_ollama_api.py` - API 调用测试
- **功能**: 测试实际的 Ollama API 调用功能
- **运行方式**: `python test_ollama_api.py`
- **测试内容**:
  - 直接 API 调用测试
  - 流式响应测试
  - 嵌入 API 测试
  - GPU 性能测试

### 3. `test_ollama_integration.py` - 完整集成测试
- **功能**: 测试 MetaGPT 与 Ollama 的完整集成
- **运行方式**: `python test_ollama_integration.py`
- **测试内容**:
  - 模块导入测试
  - 配置文件加载
  - SLC 工具库测试
  - 数据科学家角色测试
  - Ollama API 功能测试

### 4. `run_ollama_tests.py` - 测试运行脚本
- **功能**: 运行所有 Ollama 相关测试
- **运行方式**: `python run_ollama_tests.py`
- **特点**: 按顺序运行所有测试，提供统一的测试报告

## 🚀 运行测试

### 运行单个测试
```bash
# 运行基础功能测试
python tests/metagpt/provider/ollama_integration/test_ollama_basic.py

# 运行 API 调用测试
python tests/metagpt/provider/ollama_integration/test_ollama_api.py

# 运行集成测试
python tests/metagpt/provider/ollama_integration/test_ollama_integration.py
```

### 运行所有测试
```bash
# 运行完整的测试套件
python tests/metagpt/provider/ollama_integration/run_ollama_tests.py
```

### 使用 pytest 运行
```bash
# 运行所有 Ollama 测试
pytest tests/metagpt/provider/ollama_integration/

# 运行特定测试文件
pytest tests/metagpt/provider/ollama_integration/test_ollama_basic.py
```

## 📋 测试前置条件

### 1. Ollama 服务
确保 Ollama 服务正在运行：
```bash
# 启动 Ollama 服务
ollama serve

# 检查服务状态
curl http://127.0.0.1:11434/api/tags
```

### 2. 模型下载
确保测试所需的模型已下载：
```bash
# 下载测试模型
ollama pull qwen2.5:7b
ollama pull qwen2.5:32b
```

### 3. 依赖安装
确保所有依赖已安装：
```bash
pip install -r requirements.txt
pip install openai zhipuai playwright requests
```

## 📊 测试报告

测试报告位于 `tests/reports/ollama_integration_test_report.md`

报告包含：
- 测试结果摘要
- 详细测试日志
- 性能基准数据
- GPU 使用情况
- 已知问题和解决方案

## 🔧 测试配置

### 环境变量
```bash
# Ollama 服务地址
export OLLAMA_BASE_URL=http://127.0.0.1:11434

# 测试模型
export OLLAMA_TEST_MODEL=qwen2.5:7b
```

### 配置文件
测试使用 `config/config2.yaml` 中的 Ollama 配置：
```yaml
llm:
  api_type: ollama
  model: qwen2.5:32b
  base_url: http://127.0.0.1:11434/
  api_key: ""
  timeout: 600
  temperature: 0.1
```

## 🐛 故障排除

### 常见问题

1. **Ollama 服务未运行**
   ```
   错误: Connection refused
   解决: 运行 `ollama serve`
   ```

2. **模型未下载**
   ```
   错误: Model not found
   解决: 运行 `ollama pull qwen2.5:7b`
   ```

3. **依赖缺失**
   ```
   错误: No module named 'xxx'
   解决: 运行 `pip install xxx`
   ```

4. **GPU 内存不足**
   ```
   错误: CUDA out of memory
   解决: 使用更小的模型或增加 GPU 内存
   ```

### 调试模式
设置环境变量启用详细日志：
```bash
export METAGPT_LOG_LEVEL=DEBUG
export OLLAMA_DEBUG=1
```

## 📈 性能基准

### 预期性能指标
- **API 响应时间**: < 5秒
- **GPU 利用率**: > 70%
- **内存使用率**: < 80%
- **温度**: < 70°C

### 测试通过标准
- **基础功能测试**: 100% 通过
- **API 调用测试**: 100% 通过
- **集成测试**: 80% 以上通过

## 🤝 贡献指南

### 添加新测试
1. 在相应测试文件中添加新的测试函数
2. 确保测试函数有清晰的文档说明
3. 添加适当的错误处理和断言
4. 更新 README 文档

### 测试命名规范
- 测试函数名: `test_<功能>_<场景>()`
- 测试文件名: `test_<模块>_<类型>.py`
- 测试类名: `Test<模块><功能>`

### 提交测试
```bash
# 运行所有测试确保通过
python tests/metagpt/provider/ollama_integration/run_ollama_tests.py

# 提交测试代码
git add tests/metagpt/provider/ollama_integration/
git commit -m "test: 添加 Ollama 集成测试"
```

## 📞 支持

如果遇到测试问题，请：
1. 查看测试报告中的已知问题
2. 检查故障排除部分
3. 提交 Issue 到 GitHub 仓库
4. 联系开发团队

---

**注意**: 这些测试需要 Ollama 服务运行和相应的模型下载。请确保在运行测试前满足所有前置条件。 