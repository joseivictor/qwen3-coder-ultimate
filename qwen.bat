@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
python -X utf8 qwen_ultimate.py %*
