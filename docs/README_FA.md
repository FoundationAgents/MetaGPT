# MetaGPT: فریم‌ورک چندعامله

<p align="center">
<a href=""><img src="resources/MetaGPT-new-log.png" alt="لوگوی MetaGPT: GPT را در قالب یک شرکت نرم‌افزاری همکاری‌دهنده به کار بیندازید." width="150px"></a>
</p>

<p align="center">
[ <a href="../README.md">En</a> |
<a href="README_CN.md">中</a> |
<a href="README_FR.md">Fr</a> |
<a href="README_JA.md">日</a> |
<b>فا</b> ]
<b>نقش‌های مختلف به GPTها بدهید تا برای کارهای پیچیده یک تیم همکاری بسازند.</b>
</p>

<p align="center">
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
<a href="https://discord.gg/DYn29wFk9z"><img src="https://img.shields.io/badge/Join-Discord-gGnrXvVz7a?logo=discord" alt="Discord Follow"></a>
<a href="https://twitter.com/MetaGPT_"><img src="https://img.shields.io/twitter/follow/MetaGPT?style=social" alt="Twitter Follow"></a>
</p>

## MetaGPT چیست؟

MetaGPT یک **نیازمندی یک‌خطی** می‌گیرد و خروجی‌هایی مثل **داستان کاربر، تحلیل رقبا، PRD، ساختار داده، API و فایل‌های پروژه** تولید می‌کند.

درون سیستم، نقش‌هایی مثل **مدیر محصول، معمار، مدیر پروژه و مهندس** با SOPهای (رویه‌های عملیاتی استاندارد) هماهنگ کار می‌کنند.

`Code = SOP(Team)` فلسفهٔ اصلی است: SOP را عملیاتی می‌کند و روی تیمی از LLMها اعمال می‌کند.

![شرکت نرم‌افزاری متشکل از نقش‌های LLM](resources/software_company_cd.jpeg)

<p align="center">نمای کلی شرکت نرم‌افزاری چندعامله (در حال تکمیل تدریجی)</p>

## نصب

> Python **۳.۹ تا ۳.۱۱** لازم است. بررسی: `python --version`  
> با conda: `conda create -n metagpt python=3.9 && conda activate metagpt`

```bash
pip install --upgrade metagpt
metagpt --init-config   # ~/.metagpt/config2.yaml را می‌سازد
metagpt --language fa "یک بازی 2048 بساز"   # خروجی در ./workspace
```

یا با متغیر محیطی:

```bash
set METAGPT_LANG=fa
metagpt "یک بازی 2048 بساز"
```

### پیکربندی فارسی

فایل `~/.metagpt/config2.yaml`:

```yaml
language: "Persian"   # یا fa / Farsi / فارسی

llm:
  api_type: "openai"
  model: "gpt-4-turbo"
  base_url: "https://api.openai.com/v1"
  api_key: "YOUR_API_KEY"
```

### استفاده به‌عنوان کتابخانه

```python
from metagpt.software_company import generate_repo

repo_path = generate_repo("یک بازی 2048 بساز", language="Persian")
print(repo_path)
```

### Data Interpreter

```python
import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter

async def main():
    di = DataInterpreter()
    await di.run("تحلیل داده مجموعه Iris در sklearn، همراه با نمودار")

asyncio.run(main())
```

راهنمای نصب CLI: [cli_install_fa.md](install/cli_install_fa.md)

## پشتیبانی فارسی

MetaGPT از فارسی در این بخش‌ها پشتیبانی می‌کند:

| بخش | وضعیت |
|-----|--------|
| README و راهنمای نصب | فارسی |
| CLI (`--language fa` / `METAGPT_LANG=fa`) | فارسی |
| تشخیص زبان در RoleZero | فارسی + fallback از config |
| تحلیل نیازمندی | مثال فارسی |
| تعامل انسانی (human interaction) | فارسی |
| خروجی عامل‌ها | با نیازمندی فارسی یا `language: Persian` |

## آموزش و مستندات

- [مستندات انگلیسی](https://docs.deepwisdom.ai/main/en/)
- [شروع سریع](https://docs.deepwisdom.ai/main/en/guide/get_started/quickstart.html)
- [آموزش عامل](https://docs.deepwisdom.ai/main/en/guide/tutorials/agent_101.html)

## پشتیبانی

- [Discord](https://discord.gg/ZRHeExS6xv)
- [Issues در GitHub](https://github.com/FoundationAgents/MetaGPT/issues)

## ارجاع

```bibtex
@inproceedings{hong2024metagpt,
      title={Meta{GPT}: Meta Programming for A Multi-Agent Collaborative Framework},
      author={Sirui Hong and Mingchen Zhuge and Jonathan Chen and others},
      booktitle={The Twelfth International Conference on Learning Representations},
      year={2024},
      url={https://openreview.net/forum?id=VtmBAGCN7o}
}
```
