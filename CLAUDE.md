# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 代码结构（大图）
- 入口与配置：`metagpt/config2.py` 定义配置模型与默认加载逻辑（Config/CLIParams）
- 消息与数据模型：`metagpt/schema.py` 定义 Message/Document 等基础结构，序列化与资源解析逻辑
- 角色与动作：`metagpt/roles/__init__.py` 汇总核心角色；`metagpt/actions/__init__.py` 汇总动作类型与索引
- 团队与执行：`metagpt/team.py` 组织角色与环境，驱动多轮运行与归档
- LLM 提供方：`metagpt/provider/__init__.py` 汇总多种模型提供方实现

## 强约束
Python解释器路径：/home/mnt/zhangzeyuan/.conda/envs/Multinnium/bin/python