#!/bin/bash
echo "获取根路径"
#当前目录
APP_BASE=$(cd "$(dirname "$0")"; pwd)
echo "根路径是:"$APP_BASE
PYTHON_PATH=$APP_BASE/lib/python3.9
MAIN_PATH=$APP_BASE/lib
# 运行主程序
$PYTHON_PATH/bin/python3 $MAIN_PATH/main.py