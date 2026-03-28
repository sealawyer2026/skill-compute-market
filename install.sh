#!/bin/bash
# Token算力市场 Skill 安装脚本

set -e

echo "🚀 安装 Token算力市场 Skill..."
echo ""

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 需要Python3"
    exit 1
fi

# 检查requests库
if ! python3 -c "import requests" 2>/dev/null; then
    echo "📦 安装依赖: requests"
    pip3 install requests -q || pip install requests -q
fi

# 创建安装目录
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

# 复制可执行文件
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/wrapper.py" "$INSTALL_DIR/compute-market"
chmod +x "$INSTALL_DIR/compute-market"

echo "✅ 安装完成!"
echo ""
echo "使用方法:"
echo "  compute-market stats       # 查看市场统计"
echo "  compute-market providers   # 查看提供商列表"
echo "  compute-market tasks       # 查看任务列表"
echo "  compute-market --help      # 查看更多帮助"
echo ""
echo "💡 访问完整平台: http://token-master.cn/shop/"
echo ""

# 检查PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "⚠️  请将 $INSTALL_DIR 添加到PATH:"
    echo "   echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc"
    echo "   source ~/.bashrc"
fi
