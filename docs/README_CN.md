# MetaGPT: 多智能体框架

<p align="center">
<a href=""><img src="resources/MetaGPT-new-log.png" alt="MetaGPT logo: 使 GPT 以软件公司的形式工作，协作处理更复杂的任务" width="150px"></a>
</p>

<p align="center">
<b>使 GPTs 组成软件公司，协作处理更复杂的任务</b>
</p>

<p align="center">
<a href="docs/README_CN.md"><img src="https://img.shields.io/badge/文档-中文版-blue.svg" alt="CN doc"></a>
<a href="README.md"><img src="https://img.shields.io/badge/document-English-blue.svg" alt="EN doc"></a>
<a href="docs/README_JA.md"><img src="https://img.shields.io/badge/ドキュメント-日本語-blue.svg" alt="JA doc"></a>
<a href="https://discord.gg/DYn29wFk9z"><img src="https://dcbadge.vercel.app/api/server/DYn29wFk9z?style=flat" alt="Discord Follow"></a>
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
<a href="docs/ROADMAP.md"><img src="https://img.shields.io/badge/ROADMAP-路线图-blue" alt="roadmap"></a>
<a href="https://twitter.com/MetaGPT_"><img src="https://img.shields.io/twitter/follow/MetaGPT?style=social" alt="Twitter Follow"></a>
</p>

<p align="center">
   <a href="https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/geekan/MetaGPT"><img src="https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode" alt="Open in Dev Containers"></a>
   <a href="https://codespaces.new/geekan/MetaGPT"><img src="https://img.shields.io/badge/Github_Codespace-Open-blue?logo=github" alt="Open in GitHub Codespaces"></a>
   <a href="https://huggingface.co/spaces/deepwisdom/MetaGPT" target="_blank"><img alt="Hugging Face" src="https://img.shields.io/badge/%F0%9F%A4%97%20-Hugging%20Face-blue?color=blue&logoColor=white" /></a>
</p>

1. MetaGPT输入**一句话的老板需求**，输出**用户故事 / 竞品分析 / 需求 / 数据结构 / APIs / 文件等**
2. MetaGPT内部包括**产品经理 / 架构师 / 项目经理 / 工程师**，它提供了一个**软件公司**的全过程与精心调配的SOP
   1. `Code = SOP(Team)` 是核心哲学。我们将SOP具象化，并且用于LLM构成的团队

![一个完全由大语言模型角色构成的软件公司](resources/software_company_cd.jpeg)

<p align="center">软件公司多角色示意图（正在逐步实现）</p>

## 安装
<details><summary><strong>⏬ 步骤1：使用Pip安装 MetaGPT </strong><i>::点击展开::</i></summary>
<div>

> 确保您的系统上已安装Python 3.9+。您可以通过使用：`python --version`来检查这一点。  
> 您可以像这样使用conda：`conda create -n metagpt python=3.9 && conda activate metagpt`

```bash
pip install metagpt
```

</div>
</details>

<details><summary><strong>⏬ 步骤2：配置 MetaGPT </strong><i>::点击展开::</i></summary>
<div>

生成一个通用的metagpt配置文件`~/.metagpt/config2.yaml`
```bash
metagpt --init-config  
```

然后，您可以根据[配置示例](https://github.com/geekan/MetaGPT/blob/main/config/config2.example.yaml)和[配置文档](https://docs.deepwisdom.ai/main/en/guide/get_started/configuration.html)配置 `~/.metagpt/config2.yaml`：

```yaml
llm:
  api_type: "openai"  # 或 azure / ollama / open_llm 等。查看LLMType获取更多选项
  model: "gpt-4-turbo-preview"  # 或 gpt-3.5-turbo-1106 / gpt-4-1106-preview
  base_url: "https://api.openai.com/v1"  # 或 forward url /其他 llm url
  api_key: "YOUR_API_KEY"
```

</div>
</details>

<details><summary><strong>⏬ 步骤3：使用 MetaGPT </strong><i>::点击展开::</i></summary>
<div>

安装和配置完成后，您可以作为CLI使用metagpt

```bash
metagpt "Create a 2048 game"  # 这将在 ./workspace 中创建一个仓库
```

或者，您可以将其作为库使用

```python
from metagpt.software_company import generate_repo, ProjectRepo
repo: ProjectRepo = generate_repo("Create a 2048 game")  # 或 ProjectRepo("<path>")
print(repo)  # 打印带有文件的仓库结构
```

</div>
</details>


更详细的安装文档，请访问：[cli_install](https://docs.deepwisdom.ai/main/en/guide/get_started/installation.html#install-stable-version) 或 [docker_install](https://docs.deepwisdom.ai/main/en/guide/get_started/installation.html#install-with-docker)

## 快速开始的演示视频
- 在 [MetaGPT Huggingface Space](https://huggingface.co/spaces/deepwisdom/MetaGPT) 上进行体验
- [Matthew Berman: How To Install MetaGPT - Build A Startup With One Prompt!!](https://youtu.be/uT75J_KG_aY)
- [官方演示视频](https://github.com/geekan/MetaGPT/assets/2707039/5e8c1062-8c35-440f-bb20-2b0320f8d27d)

https://github.com/geekan/MetaGPT/assets/34952977/34345016-5d13-489d-b9f9-b82ace413419

## 教程
- 🗒 [在线文档](https://docs.deepwisdom.ai/main/zh/)
- 💻 [如何使用](https://docs.deepwisdom.ai/main/zh/guide/get_started/quickstart.html)  
- 🔎 [MetaGPT的能力及应用场景](https://docs.deepwisdom.ai/main/zh/guide/get_started/introduction.html)
- 🛠 如何构建你自己的智能体？
  - [MetaGPT的使用和开发教程 | 智能体入门](https://docs.deepwisdom.ai/main/zh/guide/tutorials/agent_101.html)
  - [MetaGPT的使用和开发教程 | 多智能体入门](https://docs.deepwisdom.ai/main/zh/guide/tutorials/multi_agent_101.html)
- 🧑‍💻 贡献
  - [开发路线图](ROADMAP.md)
- 🔖 示例
  - [辩论](https://docs.deepwisdom.ai/main/zh/guide/use_cases/multi_agent/debate.html)
  - [调研员](https://docs.deepwisdom.ai/main/zh/guide/use_cases/agent/researcher.html)
  - [票据助手](https://docs.deepwisdom.ai/main/zh/guide/use_cases/agent/receipt_assistant.html)
- ❓ [常见问题解答](https://docs.deepwisdom.ai/main/zh/guide/faq.html)

## 支持

### 加入我们

📢 加入我们的[Discord频道](https://discord.gg/ZRHeExS6xv)！

期待在那里与您相见！🎉

### 联系信息

如果您对这个项目有任何问题或反馈，欢迎联系我们。我们非常欢迎您的建议！

- **邮箱：** alexanderwu@deepwisdom.ai
- **GitHub 问题：** 对于更技术性的问题，您也可以在我们的 [GitHub 仓库](https://github.com/geekan/metagpt/issues) 中创建一个新的问题。

我们会在2-3个工作日内回复所有问题。

## 引用

引用 [arXiv paper](https://arxiv.org/abs/2308.00352):

```bibtex
@misc{hong2023metagpt,
      title={MetaGPT: Meta Programming for Multi-Agent Collaborative Framework},
      author={Sirui Hong and Xiawu Zheng and Jonathan Chen and Yuheng Cheng and Jinlin Wang and Ceyao Zhang and Zili Wang and Steven Ka Shing Yau and Zijuan Lin and Liyang Zhou and Chenyu Ran and Lingfeng Xiao and Chenglin Wu},
      year={2023},
      eprint={2308.00352},
      archivePrefix={arXiv},
      primaryClass={cs.AI}
}
```
