@echo off
call .venv\Scripts\activate
python -m uvicorn backend.main:app --reload --port 8000
