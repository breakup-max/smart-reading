#!/bin/bash
set -e

echo "============================================"
echo "  Smart-Reading · PDF 智能问答"
echo "============================================"
echo ""

# 检查 API Key
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "[警告] 未设置 DASHSCOPE_API_KEY 环境变量"
    echo "请执行: export DASHSCOPE_API_KEY=your-api-key"
    echo ""
    read -p "或现在输入 API Key: " KEY
    export DASHSCOPE_API_KEY="$KEY"
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

# 安装依赖（按需）
echo "[1/2] 检查依赖..."
pip show fastapi &> /dev/null || pip install -r requirements.txt

echo "[2/2] 启动服务..."
echo ""
echo "  访问地址: http://localhost:8000"
echo "  按 Ctrl+C 停止服务"
echo ""

python3 -m uvicorn web.app:app --host 0.0.0.0 --port 8000