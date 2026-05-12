#!/bin/bash
# Obsidian Vault 自动提交脚本
# 检查变动并自动提交到 git

VAULT_PATH="/mnt/f/obsidion/lukeguo"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

cd "$VAULT_PATH" || exit 1

# 检查是否有变动
if [ -n "$(git status --short)" ]; then
    echo "[$DATE] 检测到变动，开始提交..."
    
    # 添加所有变动
    git add -A
    
    # 提交
    git commit -m "obsidian: auto-sync $DATE" --quiet
    
    # 推送到远程
    git push --quiet
    
    echo "[$DATE] 提交完成: $(git log -1 --oneline)"
else
    echo "[$DATE] 无变动，跳过提交"
fi
