#!/bin/bash

# 本地测试脚本 for star_checker

echo "--- Star Checker 本地测试脚本 ---"

# 步骤 1: 检查 Python 和 pip 是否安装
if ! command -v python3 &> /dev/null
then
    echo "错误: 未找到 python3。请先安装 Python 3。"
    exit 1
fi

# 在某些系统上，pip 可能是 pip3
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null
then
    echo "错误: 未找到 pip 或 pip3。请确保已安装 pip。"
    exit 1
fi

# 决定使用 pip 还是 pip3
PIP_COMMAND="pip"
if command -v pip3 &> /dev/null
then
    PIP_COMMAND="pip3"
fi


# 步骤 2: 安装依赖
if [ -f "requirements.txt" ]; then
    echo "正在安装依赖 from requirements.txt..."
    $PIP_COMMAND install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "依赖安装失败。请检查错误信息。"
        exit 1
    fi
else
    echo "警告: 未找到 requirements.txt 文件。跳过依赖安装。"
fi

# 步骤 3: 检查 .env 文件
# 参考 readme.md, 本地运行需要 .env 文件
if [ ! -f ".env" ]; then
    echo "错误: 未找到 .env 配置文件。"
    echo "本地运行需要一个 .env 文件来提供 GitHub token 和用户名。"
    echo "已根据 readme.md 的说明为您创建了一个模板文件: .env.example"
    
    # 创建 .env.example
    cat > .env.example << EOL
# 请将此文件重命名为 .env 并填入您的信息
# 详情请参考 readme.md

# 您的 GitHub Personal Access Token (PAT)
# 需要的权限: 'repo' 和 'read:user'
GITHUB_TOKEN="your_personal_access_token"

# 您的 GitHub 用户名
GITHUB_REPOSITORY_OWNER="your_github_username"
EOL

    echo "请编辑 .env.example 文件，填入您的真实信息，然后将其重命名为 .env"
    echo "例如: mv .env.example .env"
    exit 1
fi

echo ".env 文件已找到。准备运行主脚本..."

# 步骤 4: 运行 Python 脚本
echo "---"
echo "正在运行 check_stars.py..."
python3 check_stars.py
echo "---"


if [ $? -eq 0 ]; then
    echo "✅ 脚本执行成功。"
else
    echo "❌ 脚本执行失败。请检查上面的错误输出。"
fi

echo "--- Star Checker 本地测试脚本执行完毕 ---"
