# نصب MetaGPT از خط فرمان (فارسی)

## پیش‌نیازها

- Python 3.9، 3.10 یا 3.11
- [Node.js](https://nodejs.org/) و [pnpm](https://pnpm.io/)
- کلید API برای مدل زبانی (OpenAI، Azure، Ollama و غیره)

## نصب

```bash
pip install --upgrade metagpt
```

یا از سورس:

```bash
git clone https://github.com/FoundationAgents/MetaGPT.git
cd MetaGPT
pip install --upgrade -e .
```

## پیکربندی

```bash
metagpt --init-config
```

فایل `~/.metagpt/config2.yaml` را ویرایش کنید:

```yaml
language: "Persian"

llm:
  api_type: "openai"
  model: "gpt-4-turbo"
  base_url: "https://api.openai.com/v1"
  api_key: "YOUR_API_KEY"
```

## اجرا به فارسی

```bash
# روش ۱: فلگ زبان
metagpt --language fa "یک بازی مار با پایتون بساز"

# روش ۲: متغیر محیطی (رابط CLI هم فارسی می‌شود)
set METAGPT_LANG=fa
metagpt "یک اپلیکیشن todo بساز"
```

## خروجی

پروژه در پوشه `./workspace` ساخته می‌شود.

## عیب‌یابی

| مشکل | راه‌حل |
|------|--------|
| `Missing argument 'IDEA'` | ایده را داخل کوتیشن بنویسید |
| خروجی انگلیسی | `language: Persian` در config یا `--language fa` |
| خطای API | `base_url` و `api_key` را بررسی کنید |

مستندات کامل: [README_FA.md](../README_FA.md)
