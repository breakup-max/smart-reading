@echo off
chcp 65001 >nul
title Smart-Reading

echo ============================================
echo   Smart-Reading · PDF 智能问答
echo ============================================
echo.

:: 检查 API Key
if "%DASHSCOPE_API_KEY%"=="" (
    echo [警告] 未设置 DASHSCOPE_API_KEY 环境变量
    echo.
    set /p KEY="请输入通义千问 API Key: "
    set DASHSCOPE_API_KEY=%KEY%
    echo.
)

:: 检查依赖
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [1/2] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

echo [2/2] 启动服务...
echo.
echo   访问地址: http://localhost:8000
echo   按 Ctrl+C 停止服务
echo.

python -m uvicorn web.app:app --host 0.0.0.0 --port 8000

pause