#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Localized UI strings for MetaGPT CLI and human interaction."""

from typing import Optional

PERSIAN_ALIASES = frozenset(
    {
        "fa",
        "fa_ir",
        "fa-ir",
        "persian",
        "farsi",
        "فارسی",
        "پارسی",
    }
)

ENGLISH_ALIASES = frozenset({"en", "en_us", "en-us", "english"})

MESSAGES = {
    "English": {
        "missing_idea": "Missing argument 'IDEA'. Run 'metagpt --help' for more information.",
        "config_backed_up": "Existing configuration file backed up at {path}",
        "config_initialized": "Configuration file initialized at {path}",
        "multilines_input_hint": "Enter your content, use Ctrl-D or Ctrl-Z (windows) to save it.",
        "input_type_error": "Input content can't meet required_type: {req_type}, please Re-Enter.",
        "input_num_prompt": "Enter the num of the interaction key: ",
        "interact_header": (
            "\n{interact_type} interaction\n"
            "Interaction data: {fields}\n"
            "Enter the num to interact with corresponding field or `q`/`quit`/`exit` to stop interaction.\n"
            "Enter the field content until it meet field required type.\n"
        ),
        "interact_stop": "Stop human interaction",
        "interact_field": "You choose to interact with field: {field}, and do a `{interact_type}` operation.",
        "review_prompt": "Enter your review comment: ",
        "revise_prompt": "Enter your revise content: ",
        "cli_startup_help": "Start a new project.",
        "cli_idea_help": "Your innovative idea, such as 'Create a 2048 game.'",
        "cli_investment_help": "Dollar amount to invest in the AI company.",
        "cli_n_round_help": "Number of rounds for the simulation.",
        "cli_code_review_help": "Whether to use code review.",
        "cli_run_tests_help": "Whether to enable QA for adding & running tests.",
        "cli_implement_help": "Enable or disable code implementation.",
        "cli_project_name_help": "Unique project name, such as 'game_2048'.",
        "cli_inc_help": "Incremental mode. Use it to coop with existing repo.",
        "cli_project_path_help": "Directory path of the old version project for incremental requirements.",
        "cli_reqa_file_help": "Source file name for rewriting the quality assurance code.",
        "cli_max_auto_summarize_help": (
            "Maximum auto-invocations of 'SummarizeCode' (-1 = unlimited). For debugging."
        ),
        "cli_recover_path_help": "Recover the project from existing serialized storage.",
        "cli_init_config_help": "Initialize the configuration file for MetaGPT.",
        "cli_language_help": "UI language: English or Persian (fa). Also set via METAGPT_LANG or config language.",
        "cli_startup_desc": "Run a startup. Be a boss.",
    },
    "Persian": {
        "missing_idea": "آرگومان «IDEA» وارد نشده است. برای راهنما دستور «metagpt --help» را اجرا کنید.",
        "config_backed_up": "فایل پیکربندی قبلی در {path} پشتیبان‌گیری شد.",
        "config_initialized": "فایل پیکربندی در {path} ایجاد شد.",
        "multilines_input_hint": "متن خود را وارد کنید. برای ذخیره از Ctrl-D یا Ctrl-Z (ویندوز) استفاده کنید.",
        "input_type_error": "ورودی با نوع موردنیاز ({req_type}) سازگار نیست. دوباره وارد کنید.",
        "input_num_prompt": "شماره فیلد تعاملی را وارد کنید: ",
        "interact_header": (
            "\nتعامل {interact_type}\n"
            "داده‌های تعامل: {fields}\n"
            "شماره فیلد را وارد کنید یا با `q`/`quit`/`exit` تعامل را متوقف کنید.\n"
            "محتوای فیلد را تا رسیدن به نوع صحیح وارد کنید.\n"
        ),
        "interact_stop": "تعامل با کاربر متوقف شد",
        "interact_field": "فیلد «{field}» انتخاب شد. عملیات «{interact_type}» انجام می‌شود.",
        "review_prompt": "نظر بازبینی خود را وارد کنید: ",
        "revise_prompt": "متن اصلاح‌شده را وارد کنید: ",
        "cli_startup_help": "شروع یک پروژه جدید.",
        "cli_idea_help": "ایدهٔ نوآورانهٔ شما، مثلاً «یک بازی 2048 بساز».",
        "cli_investment_help": "مبلغ سرمایه‌گذاری (دلار) در شرکت هوش مصنوعی.",
        "cli_n_round_help": "تعداد دورهای شبیه‌سازی.",
        "cli_code_review_help": "فعال‌سازی بازبینی کد.",
        "cli_run_tests_help": "فعال‌سازی QA برای افزودن و اجرای تست‌ها.",
        "cli_implement_help": "فعال یا غیرفعال کردن پیاده‌سازی کد.",
        "cli_project_name_help": "نام یکتا برای پروژه، مثلاً game_2048.",
        "cli_inc_help": "حالت افزایشی؛ برای همکاری با مخزن موجود.",
        "cli_project_path_help": "مسیر پروژهٔ قبلی برای نیازمندی‌های افزایشی.",
        "cli_reqa_file_help": "نام فایل منبع برای بازنویسی کد تضمین کیفیت.",
        "cli_max_auto_summarize_help": "حداکثر اجرای خودکار SummarizeCode (‎-1 = نامحدود). برای دیباگ.",
        "cli_recover_path_help": "بازیابی پروژه از حافظهٔ سریال‌شده.",
        "cli_init_config_help": "ایجاد فایل پیکربندی MetaGPT.",
        "cli_language_help": "زبان رابط: English یا Persian (fa). از METAGPT_LANG یا language در config هم پشتیبانی می‌شود.",
        "cli_startup_desc": "اجرای استارتاپ. رئیس باشید.",
    },
}


def normalize_language(lang: Optional[str]) -> str:
    """Map locale aliases to canonical language names."""
    if not lang:
        return "English"
    key = lang.strip().lower().replace(" ", "_")
    if key in PERSIAN_ALIASES or lang.strip() in PERSIAN_ALIASES:
        return "Persian"
    if key in ENGLISH_ALIASES:
        return "English"
    if lang.strip() in ("Persian", "English", "Chinese", "French", "Japanese"):
        return lang.strip()
    return lang.strip() or "English"
