#!/bin/bash
# Git Commit Tracker - 团队代码提交日报
# 每天20:00自动执行，统计当日代码提交情况

set -e

# ============================================
# 配置加载
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.sh"

# 加载配置文件（如果存在）
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# 设置默认值
GIT_REPO_PATH="${GIT_REPO_PATH:-/path/to/your/git/repo}"
GIT_BRANCHES="${GIT_BRANCHES:-}"
OBSIDIAN_BRANCH_FILE="${OBSIDIAN_BRANCH_FILE:-01-项目/在执行项目git分支汇总.md}"
DEFAULT_BRANCHES="${DEFAULT_BRANCHES:-main}"
OBSIDIAN_VAULT_PATH="${OBSIDIAN_VAULT_PATH:-/mnt/f/.openclaw/workspace/obsidian-vault}"
OBSIDIAN_DAILY_DIR="${OBSIDIAN_DAILY_DIR:-05-日记}"
REPORT_SUBDIR="${REPORT_SUBDIR:-git-reports}"

# 报告配置
REPORT_DATE=$(date +%Y-%m-%d)
# 统计时间段：昨天20:00到今天20:00
REPORT_SINCE_DATE=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
REPORT_UNTIL_DATE=$(date +%Y-%m-%d)

# ============================================
# 颜色定义
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# ============================================
# 检查依赖
# ============================================
check_dependencies() {
    log_info "检查依赖..."

    if ! command -v git &> /dev/null; then
        log_error "未找到 git 命令"
        exit 1
    fi

    log_success "依赖检查完成"
}

# ============================================
# 从远程仓库获取分支是否存在
# 如果网络不可达，检查本地缓存的远程分支
# ============================================
remote_branch_exists() {
    local branch="$1"
    cd "$GIT_REPO_PATH" 2>/dev/null || return 1

    # 先尝试获取最新分支信息（如果网络可达）
    if timeout 20 git fetch origin "$branch" 2>/dev/null; then
        # 检查远程分支是否存在
        timeout 10 git ls-remote --heads origin "$branch" 2>/dev/null | grep -q "refs/heads/${branch}$"
    else
        # 网络不可达，检查本地缓存的远程分支
        git show-ref --verify --quiet "refs/remotes/origin/${branch}" 2>/dev/null
    fi
}

# ============================================
# 获取匹配前缀的所有远程分支
# 如果网络不可达，使用本地缓存的远程分支列表
# ============================================
get_branches_by_prefix() {
    local prefix="$1"
    cd "$GIT_REPO_PATH" 2>/dev/null || return

    # 尝试从远程获取分支列表（如果网络可达）
    if timeout 15 git ls-remote --heads origin 2>/dev/null >/dev/null; then
        # 获取所有远程分支名（refs/heads/后部分）
        timeout 15 git ls-remote --heads origin 2>/dev/null | \
            sed 's|.*refs/heads/||' | \
            grep "^${prefix}"
    else
        # 网络不可达，使用本地缓存的远程分支列表
        git branch -r 2>/dev/null | \
            sed 's|origin/||' | \
            sed 's/^[[:space:]]*//' | \
            grep "^${prefix}"
    fi
}

# ============================================
# 从Obsidian文件读取配置（分支和人员）
# 支持格式:
#   ## 当前跟踪的分支
#   - main                    # 完整分支名，精确匹配
#   - dev-                    # 分支前缀，匹配所有 dev- 开头的分支（如 dev-3.11.0.0, dev-3.12.0.0）
#   - feature-                # 分支前缀，匹配所有 feature- 开头的分支
#
#   ## 统计人员范围（可选）
#   - 张三
#   - 李四
#
# 或:
#   # 在行分支
#   dev-3.11.0.0
#   main
#   dev-                    # 前缀匹配模式
#
#   # 团队成员
#   王俊
#   王浩
# ============================================
read_config_from_obsidian() {
    local config_file="${OBSIDIAN_VAULT_PATH}/${OBSIDIAN_BRANCH_FILE}"
    local mode=""  # branches | authors
    local branches=""
    local authors=""

    if [ ! -f "$config_file" ]; then
        log_warn "Obsidian配置文件不存在: $config_file"
        log_info "使用默认分支: $DEFAULT_BRANCHES"
        echo "BRANCHES:$DEFAULT_BRANCHES"
        echo "AUTHORS:"
        return
    fi

    log_info "从 Obsidian 读取配置文件: $OBSIDIAN_BRANCH_FILE"

    # 逐行解析文件
    while IFS= read -r line; do
        # 检测区块标题（支持多种格式）
        if [[ "$line" =~ ^#+[[:space:]]*(在行分支|当前跟踪的分支|分支) ]]; then
            mode="branches"
            continue
        elif [[ "$line" =~ ^#+[[:space:]]*(团队成员|统计人员|人员) ]]; then
            mode="authors"
            continue
        fi

        # 跳过空行和分隔符
        [[ -z "$line" ]] && continue
        [[ "$line" =~ ^--- ]] && continue
        # 跳过 markdown 列表标记（如 * item），但在 branches 模式下允许 * 作为通配符
        if [[ "$line" =~ ^\*[[:space:]] ]] && [ "$mode" != "branches" ]; then
            continue
        fi

        # 提取列表项（支持 - item 和纯文本格式）
        local value=""
        if [[ "$line" =~ ^-[[:space:]]+(.+)$ ]]; then
            value="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^[[:space:]]*([^-#[:space:]].*)$ ]] && [ -n "$mode" ]; then
            # 纯文本行（不以 - 开头，不是注释，有内容）
            local temp="${BASH_REMATCH[1]}"
            # 排除空行和只有空白的行
            [[ "$temp" =~ ^[[:space:]]*$ ]] && continue
            value="$temp"
        fi

        if [ -n "$value" ]; then
            value=$(echo "$value" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
            if [ -n "$value" ]; then
                if [ "$mode" = "branches" ]; then
                    branches="$branches $value"
                elif [ "$mode" = "authors" ]; then
                    authors="$authors $value"
                fi
            fi
        fi
    done < "$config_file"

    # 清理并输出
    branches=$(echo "$branches" | sed 's/^ *//' | sed 's/ *$//')
    authors=$(echo "$authors" | sed 's/^ *//' | sed 's/ *$//')

    # 如果没有分支，使用默认值
    if [ -z "$branches" ]; then
        log_warn "未从配置文件中读取到分支，使用默认值: $DEFAULT_BRANCHES"
        branches="$DEFAULT_BRANCHES"
    fi

    echo "BRANCHES:$branches"
    echo "AUTHORS:$authors"
}

# ============================================
# 获取配置（分支和人员）
# ============================================
get_config() {
    local branches=""
    local authors=""

    # 始终从 Obsidian 读取配置（分支和人员）
    local config
    config=$(read_config_from_obsidian)
    branches=$(echo "$config" | grep '^BRANCHES:' | cut -d':' -f2-)
    authors=$(echo "$config" | grep '^AUTHORS:' | cut -d':' -f2-)

    # 如果 Obsidian 没有读取到分支，使用 GIT_BRANCHES 配置或默认值
    if [ -z "$branches" ]; then
        if [ -z "$GIT_BRANCHES" ] || [ "$GIT_BRANCHES" = "*" ]; then
            branches="*"
            log_info "配置: 获取所有分支（按人员筛选）"
        else
            branches="$GIT_BRANCHES"
            log_info "使用配置中的分支列表: $branches"
        fi
    fi

    log_info "从 Obsidian 读取配置:"
    log_info "  分支: $branches"
    if [ -n "$authors" ]; then
        log_info "  人员: $authors"
    else
        log_info "  人员: 全部"
    fi

    echo "BRANCHES:$branches"
    echo "AUTHORS:$authors"
}

# ============================================
# 获取指定分支的Git提交记录（从远程）
# 注意: 此函数只输出提交数据，日志输出到stderr
# 时间范围: since_date 20:00 ~ until_date 20:00
# ============================================
get_branch_commits() {
    local branch="$1"
    local since_date="$2"
    local until_date="$3"
    local filter_authors="$4"

	# log_info " branch: $branch"
	# log_info "since_date :$since_date"
	# log_info "until_date:$until_date"
	# log_info "filter_authors:$filter_authors"

    cd "$GIT_REPO_PATH" 2>/dev/null || return

    # 先获取远程分支最新信息
    log_info "  获取分支: $branch"
    timeout 60 git fetch origin "$branch" 2>/dev/null || true
    
    # 尝试拉取远程分支最新代码到本地
    # 检查本地是否存在该分支，不存在则创建并跟踪
    if git show-ref --verify --quiet "refs/remotes/origin/${branch}" 2>/dev/null; then
        # 本地已存在远程分支，尝试更新
        if git checkout "$branch" 2>/dev/null; then
            git pull origin "$branch" 2>/dev/null || true
            git checkout - 2>/dev/null || true  # 返回原分支
        fi
    else
        # 本地不存在该分支，尝试创建并跟踪
        git checkout -b "$branch" "origin/$branch" 2>/dev/null || true
        git checkout - 2>/dev/null || true  # 返回原分支
    fi

    # 检查远程分支是否存在
    if ! timeout 10 git ls-remote --heads origin "$branch" 2>/dev/null | grep -q "$branch"; then
        return
    fi

    # 使用远程分支引用
    local branch_ref="origin/${branch}"

    # 构建作者过滤条件
    local author_filter=""
    if [ -n "$filter_authors" ]; then
        for author in $filter_authors; do
            if [ -z "$author_filter" ]; then
                author_filter="--author=${author}"
            else
                author_filter="${author_filter} --author=${author}"
            fi
        done
    fi

    # 获取提交记录（只输出数据，无日志）
    # 时间范围: since_date 20:00 ~ until_date 20:00
    if [ -n "$author_filter" ]; then
        # shellcheck disable=SC2086
        git log "${branch_ref}" --since="${since_date} 20:00:00" --until="${until_date} 20:00:00" \
            --format="%H%x00%an%x00%ad%x00%s%x00${branch}" --date=short --no-merges ${author_filter} 2>/dev/null | awk 'BEGIN {FS="\0"; OFS="|"} {print $1, $2, $3, $4, $5}' | while IFS='|' read -r hash author date message branch_name; do
            [ -z "$hash" ] && continue
            stats=$(git show --stat --format="" "$hash" 2>/dev/null | tail -1 | tr '\n' ' ')
            echo "${hash}|${author}|${date}|${message}|${stats}|${branch_name}"
        done
    else
        git log "${branch_ref}" --since="${since_date} 20:00:00" --until="${until_date} 20:00:00" \
            --format="%H%x00%an%x00%ad%x00%s%x00${branch}" --date=short --no-merges 2>/dev/null | awk 'BEGIN {FS="\0"; OFS="|"} {print $1, $2, $3, $4, $5}' | while IFS='|' read -r hash author date message branch_name; do
            [ -z "$hash" ] && continue
            stats=$(git show --stat --format="" "$hash" 2>/dev/null | tail -1 | tr '\n' ' ')
            echo "${hash}|${author}|${date}|${message}|${stats}|${branch_name}"
        done
    fi
}

# ============================================
# 获取所有分支的提交记录（从远程）
# 支持分支名和分支名前缀（如 dev-）
# 当 branches 为空或 "*" 时，获取所有分支
# ============================================
get_all_commits() {
    local since_date="$1"
    local until_date="$2"
    local branches="$3"
    local authors="$4"
    local all_commits=""

    # 确保我们在正确的目录
    if [ ! -d "$GIT_REPO_PATH/.git" ]; then
        log_error "Git仓库路径无效: $GIT_REPO_PATH"
        exit 1
    fi

    cd "$GIT_REPO_PATH"

    # 检查是否需要获取所有分支（branches 为空或 "*"）
    if [ -z "$branches" ] || [ "$branches" = "*" ]; then
        log_info "获取所有分支的提交记录（按人员筛选）"
        
        # 先从远程仓库获取所有分支的最新代码
        log_info "从远程仓库获取最新代码..."
        if timeout 120 git fetch --all 2>&1; then
            log_success "远程代码同步完成"
        else
            log_warn "远程代码同步失败，使用本地缓存"
        fi
        
        # 构建作者过滤条件
        local author_filter=""
        if [ -n "$authors" ]; then
            for author in $authors; do
                if [ -z "$author_filter" ]; then
                    author_filter="--author=$author"
                else
                    author_filter="$author_filter --author=$author"
                fi
            done
        fi
        
        # 获取所有分支的提交
        local git_cmd="git log --all --since=\"${since_date} 20:00:00\" --until=\"${until_date} 20:00:00\" --format=\"%H%x00%an%x00%ad%x00%s%x00%D\" --date=short --no-merges $author_filter 2>/dev/null"
        
        local raw_commits
        raw_commits=$(eval "$git_cmd" | awk 'BEGIN {FS="\0"; OFS="|"} {print $1, $2, $3, $4, $5}')
        
        # 解析提交并添加分支信息和代码统计
        echo "$raw_commits" | while IFS='|' read -r hash author date message branch_ref; do
            if [ -n "$hash" ] && [ ${#hash} -ge 10 ]; then
                # 从 ref 中提取分支名
                local branch_name=""
                if [ -n "$branch_ref" ]; then
                    branch_name=$(echo "$branch_ref" | grep -oE 'origin/[^,]+' | head -1 | sed 's|origin/||')
                fi
                
                # 获取代码行数统计
                local stats=""
                stats=$(git show --stat --format="" "$hash" 2>/dev/null | tail -1 | tr '\n' ' ')
                
                echo "$hash|$author|$date|$message|$stats|$branch_name"
            fi
        done
        
        log_info "总共获取到 $(echo "$raw_commits" | grep -v '^$' | wc -l) 条提交记录"
        return
    fi

    # 原有逻辑：按指定分支获取提交
    for branch_config in $branches; do
        local matched_branches=""

        # 判断是完整分支名还是前缀
        if remote_branch_exists "$branch_config"; then
            # 是完整分支名，直接使用
            matched_branches="$branch_config"
            log_info "  - 完整分支: $branch_config"
        else
            # 尝试作为前缀匹配
            matched_branches=$(get_branches_by_prefix "$branch_config")
            if [ -n "$matched_branches" ]; then
                log_info "  - 前缀 '$branch_config' 匹配到分支:"
                echo "$matched_branches" | while read -r mb; do
                    [ -n "$mb" ] && log_info "      - $mb"
                done
            else
                log_warn "  - 未找到匹配 '$branch_config' 的分支（非完整分支名，也未匹配到前缀）"
                continue
            fi
        fi
        log_info "匹配到的分支：$matched_branches"
        # 遍历所有匹配的分支获取提交记录
        for branch in $matched_branches; do
            # 获取分支提交（抑制日志输出）
			#log_info "获取branch_commits：$get_branch_commits "$branch" "$since_date" "$until_date" "$authors" "
            branch_commits=$(get_branch_commits "$branch" "$since_date" "$until_date" "$authors" 2>/dev/null)
            log_info "  - 分支 '$branch' 获取到 $(echo "$branch_commits" | grep -v '^$' | wc -l) 条提交"
            if [ -n "$branch_commits" ]; then
                if [ -z "$all_commits" ]; then
                    all_commits="$branch_commits"
                else
                    all_commits="${all_commits}
${branch_commits}"
                fi
            fi
        done
    done
    
	# log_info "匹配到的commit：$all_commits"
    log_info "总共获取到 $(echo "$all_commits" | grep -v '^$' | wc -l) 条提交记录"
    echo "$all_commits"
}

# ============================================
# 代码审查功能
# ============================================

# 代码审查模式检测
declare -A REVIEW_PATTERNS=(
    # Bug 相关模式
    ["TODO_存在TODO待办"]="TODO"
    ["FIXME_存在FIXME待修复问题"]="FIXME"
    ["XXX_存在XXX警告"]="XXX"
    ["HACK_存在HACK代码"]="HACK"
    ["空Catch_空catch块可能导致异常吞没"]="catch\s*\{\s*\}"
    ["SystemOut_println_存在System.out.println调试语句"]="System\.out\.print"
    ["ConsoleLog_存在console.log调试语句"]="console\.log"
    ["Println_存在print调试语句"]="println"
    ["空方法_空方法体需要实现"]="\{\s*\}\s*;?\s*$"
    ["硬编码密码_硬编码密码存在安全风险"]="password\s*=\s*[\"']"
    ["硬编码密钥_硬编码密钥存在安全风险"]="api[_-]?key\s*=\s*[\"']"
    ["SQL注入风险_SQL语句使用字符串拼接"]="\+.*SELECT.*\+|\+.*INSERT.*\+|\+.*UPDATE.*\+|\+.*DELETE.*\+"
    ["未关闭资源_流或连接未显式关闭"]="new\s+File(Input|Output)Stream|new\s+Connection"
    ["ThreadSleep_Thread.sleep可能阻塞线程"]="Thread\.sleep"
    ["空指针风险_nullable参数未做空检查"]="\.getClass\(\)|\.toString\(\)|\.hashCode\(\)|\.equals\("

    # 优化相关模式
    ["String拼接到处使用String拼接影响性能"]="\+=.*String|new\s+String\("
    ["ArrayList初始化_未指定初始容量可能频繁扩容"]="new\s+ArrayList\(\)"
    ["HashMap初始化_未指定初始容量可能频繁扩容"]="new\s+HashMap\(\)"
    ["循环内String拼接_循环内String拼接影响性能"]="for.*\{[^}]*\+="
    ["不必要的自动装箱_可能产生额外对象"]="new\s+Integer\(|new\s+Long\(|new\s+Double\(|new\s+Float\(|new\s+Boolean\("
    ["正则预编译_正则未预编译影响性能"]="Pattern\.compile|Matcher\.match"
    ["日志级别判断_未判断日志级别直接拼接"]="logger\.debug.*\+|logger\.trace.*\+"
    ["stream顺序遍历_可以使用forEach替代"]="\.stream\(\)\.forEach"
    ["Optional滥用_过度使用Optional"]="Optional\.of"
)

# 代码审查函数
perform_code_review() {
    local commit_hash="$1"
    local branch="$2"
    local review_results=""

    cd "$GIT_REPO_PATH" 2>/dev/null || return ""

    # 获取提交的详细diff
    local diff_content
    diff_content=$(git show "$commit_hash" --no-color -p 2>/dev/null | head -500) || return ""

    # 检查各种模式
    for pattern_key in "${!REVIEW_PATTERNS[@]}"; do
        local pattern="${REVIEW_PATTERNS[$pattern_key]}"
        local category="${pattern_key%%_*}"
        local description="${pattern_key#*_}"

        if echo "$diff_content" | grep -iqE "$pattern"; then
            # 检查是否在新增代码中（以+开头的行）
            local matched_lines
            matched_lines=$(echo "$diff_content" | grep -iE "$pattern" | grep -E "^\+" | head -3)

            if [ -n "$matched_lines" ]; then
                if [ -z "$review_results" ]; then
                    review_results="**${category}**: ${description}"
                else
                    review_results="${review_results}\n**${category}**: ${description}"
                fi
            fi
        fi
    done

    # 检查新增代码行数是否过多（可能需要review）
    local lines_added
    lines_added=$(echo "$diff_content" | grep -E "^\+" | grep -v "^+++" | wc -l)
    if [ "$lines_added" -gt 200 ]; then
        review_results="${review_results}\n**大改动**: 单次提交新增${lines_added}行，建议仔细review"
    fi

    # 检查删除代码行数是否过多
    local lines_removed
    lines_removed=$(echo "$diff_content" | grep -E "^\-" | grep -v "^---" | wc -l)
    if [ "$lines_removed" -gt 200 ]; then
        review_results="${review_results}\n**大删除**: 单次提交删除${lines_removed}行，注意回归风险"
    fi

    echo -e "$review_results"
}

# 为所有提交生成代码审查
generate_code_reviews() {
    local commits_data="$1"
    local reviews=""

    while IFS='|' read -r hash author date message stats branch; do
        [ -z "$hash" ] && continue
        # 跳过无效提交
        if [ ${#hash} -lt 10 ]; then
            continue
        fi

        local review
        review=$(perform_code_review "$hash" "$branch")

        if [ -n "$review" ]; then
            reviews="${reviews}\n### 🔍 代码审查: ${message:0:50}...

${review}

---
"
        fi
    done <<< "$commits_data"

    echo -e "$reviews"
}

# ============================================
# 解析提交信息
# ============================================
parse_commit_message() {
    local message="$1"
    local type="other"
    local item_id=""

    if [[ "$message" =~ ^(fix|bug|修复|fix:|bugfix:|bug:|Bug:|BUG:) ]]; then
        type="bug"
        if [[ "$message" =~ [#]([0-9]+) ]] || [[ "$message" =~ [Bb]ug[-_]?([0-9]+) ]]; then
            item_id="bug-${BASH_REMATCH[1]}"
        fi
    elif [[ "$message" =~ ^(feat|feature|新增|功能|feat:|feature:) ]]; then
        type="feature"
        if [[ "$message" =~ [#]([0-9]+) ]] || [[ "$message" =~ [Ff]eat[-_]?([0-9]+) ]]; then
            item_id="feat-${BASH_REMATCH[1]}"
        fi
    elif [[ "$message" =~ ^(docs|doc|文档) ]]; then
        type="docs"
    elif [[ "$message" =~ ^(refactor|重构) ]]; then
        type="refactor"
    elif [[ "$message" =~ ^(test|测试) ]]; then
        type="test"
    elif [[ "$message" =~ ^(chore|构建|ci|CI) ]]; then
        type="chore"
    fi

	if [[ "$type" != "other" ]]; then
		echo "${type}|${item_id}"
	fi
}

# ============================================
# 判断是否AI提交（通过提交消息中的关键字）
# 支持多种格式: [AICODe], AICODe, Aic, AI 等
# ============================================
is_ai_commit() {
    local message="$1"
    # 不区分大小写匹配 AI 相关关键字
    if echo "$message" | grep -qiE '\[?AICode\]?|\[?Aic\]?|\[?AI\s*Coding\]?|AI辅助|AI代写|AIGC'; then
        return 0  # 是AI提交
    fi
    return 1  # 非AI提交
}

# ============================================
# 生成Markdown报告
# ============================================
generate_markdown_report() {
    local commits_data="$1"
    local report_date="$2"
    local branches_list="$3"
    local authors_list="$4"

    local report=""

    # 报告头
    report="# 📊 团队代码提交日报

**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')
**统计范围**: ${REPORT_SINCE_DATE} 20:00 ~ ${REPORT_UNTIL_DATE} 20:00
**跟踪分支**: ${branches_list}
"

    if [ -n "$authors_list" ]; then
        report+="**统计人员**: ${authors_list}
"
    else
        report+="**统计人员**: 全部
"
    fi

    report+="
---

"

    if [ -z "$commits_data" ]; then
        report+="## 📭 今日无提交记录

暂无代码提交数据。

"
    else
        # 统计概览
        local total_commits=$(echo "$commits_data" | grep -v '^$' | wc -l)
        local total_authors=$(echo "$commits_data" | grep -v '^$' | cut -d'|' -f2 | sort -u | wc -l)
        local total_branches=$(echo "$commits_data" | grep -v '^$' | cut -d'|' -f6 | sort -u | wc -l)

        report+="## 📈 概览

| 指标 | 数值 |
|------|------|
| 总提交数 | ${total_commits} |
| 参与人数 | ${total_authors} |
| 涉及分支 | ${total_branches} |

---

"

        # 按分支统计
        report+="## 🌿 分支提交统计

"

        declare -A branch_commits
        while IFS='|' read -r hash author date message stats branch; do
            [ -z "$branch" ] && continue
            branch_commits["$branch"]=$((${branch_commits["$branch"]:-0} + 1))
        done <<< "$commits_data"

        report+="| 分支 | 提交数 |
|------|--------|
"
        for branch in "${!branch_commits[@]}"; do
            report+="| ${branch} | ${branch_commits[$branch]} |
"
        done

        report+="
---

"

        # 按人员统计
        report+="## 👥 个人提交统计

"

        declare -A author_commits
        declare -A author_stats
        declare -A author_ai_commits
        declare -A author_lines_added
        declare -A author_lines_removed
        declare -A author_branches

        while IFS='|' read -r hash author date message stats branch; do
            [ -z "$author" ] && continue
            author_commits["$author"]=$((${author_commits["$author"]:-0} + 1))

            # 统计AI提交
            if is_ai_commit "$message"; then
                author_ai_commits["$author"]=$((${author_ai_commits["$author"]:-0} + 1))
            fi

            # 记录分支信息
            if [ -n "$branch" ]; then
                local existing_branches="${author_branches[$author]}"
                if [[ ",$existing_branches," != *",$branch,"* ]]; then
                    if [ -z "$existing_branches" ]; then
                        author_branches["$author"]="$branch"
                    else
                        author_branches["$author"]="$existing_branches,$branch"
                    fi
                fi
            fi

            # 解析代码行数变化
            if [ -n "$stats" ]; then
                local lines_add=0
                local lines_del=0
                lines_add=$(echo "$stats" | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' | head -1 || echo "0")
                lines_del=$(echo "$stats" | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' | head -1 || echo "0")
                [ -z "$lines_add" ] && lines_add=0
                [ -z "$lines_del" ] && lines_del=0
                author_lines_added["$author"]=$((${author_lines_added["$author"]:-0} + lines_add))
                author_lines_removed["$author"]=$((${author_lines_removed["$author"]:-0} + lines_del))
            fi

            parsed=$(parse_commit_message "$message")
            type=$(echo "$parsed" | cut -d'|' -f1)

            if [ -z "${author_stats[$author]}" ]; then
                author_stats["$author"]="${type}"
            else
                author_stats["$author"]+=",${type}"
            fi
        done <<< "$commits_data"

        report+="| 成员 | 提交数 | AI提交 | AI占比 | 涉及分支 | 代码增(+) | 代码删(-) |
|------|--------|--------|--------|----------|----------|----------|
"

        for author in "${!author_commits[@]}"; do
            local count=${author_commits["$author"]}
            local ai_count=${author_ai_commits["$author"]:-0}
            local ai_percent=0
            if [ "$count" -gt 0 ]; then
                ai_percent=$((ai_count * 100 / count))
            fi
            local branches=${author_branches["$author"]:-}
            local lines_add=${author_lines_added["$author"]:-0}
            local lines_del=${author_lines_removed["$author"]:-0}

            report+="| ${author} | ${count} | ${ai_count} | ${ai_percent}% | ${branches} | +${lines_add} | -${lines_del} |
"
        done

        report+="
---

"

        # 详细提交列表
        report+="## 📝 详细提交列表

"

        # 过滤掉包含ANSI码的无效提交，只保留有效的git提交记录
        # 有效记录格式: hash|author|date|message|stats|branch
        commits_data=$(echo "$commits_data" | grep -v '\x1b\[' | grep -v '^\[' | grep -v '^$' | grep -E '^[a-f0-9]{6,40}\|[^|]+\|[0-9]{4}-[0-9]{2}-[0-9]{2}\|')

        # 初始化代码审查汇总
        local review_issues_count=0
        local review_summary=""

        while IFS='|' read -r hash author date message stats branch; do
            [ -z "$hash" ] && continue
            # 跳过无效提交（hash太短或包含非hex字符）
            if [ ${#hash} -lt 10 ] || ! echo "$hash" | grep -qE '^[a-f0-9]+$'; then
                continue
            fi

            parsed=$(parse_commit_message "$message")
            type=$(echo "$parsed" | cut -d'|' -f1)
            item_id=$(echo "$parsed" | cut -d'|' -f2)

            local badge=""
            case "$type" in
                bug) badge="🐛 [Bug]" ;;
                feature) badge="✨ [Feature]" ;;
                docs) badge="📚 [Docs]" ;;
                refactor) badge="🔨 [Refactor]" ;;
                test) badge="🧪 [Test]" ;;
                chore) badge="⚙️ [Chore]" ;;
                *) badge="📝 [Other]" ;;
            esac

            report+="### ${badge} ${message}

- **作者**: ${author}
- **分支**: ${branch}
- **时间**: ${date}
- **Hash**: \`${hash:0:8}\`
"

            if [ -n "$item_id" ]; then
                report+="- **关联**: ${item_id}
"
            fi

            if [ -n "$stats" ]; then
                report+="- **改动**: ${stats}
"
            fi

            # 对每个提交进行代码审查，并将结果直接放在提交下方
            local commit_review
            commit_review=$(perform_code_review "$hash" "$branch")
            if [ -n "$commit_review" ]; then
                report+="
> 🔍 代码审查:
$(echo "$commit_review" | sed 's/^/> /')
"
                # 汇总问题
                review_issues_count=$(($review_issues_count + 1))
                review_summary="${review_summary}
- **${message:0:40}...**: ${commit_review}"
            fi

            report+="
"
        done <<< "$commits_data"

        # 添加代码审查汇总
        if [ $review_issues_count -gt 0 ]; then
            report+="
---

## 🔍 代码审查汇总

共发现 **${review_issues_count}** 个提交存在潜在问题:

${review_summary}

"
        fi
    fi

    report+="---

*报告由 OpenClaw Git Commit Tracker 自动生成*
"

    echo "$report"
}

# ============================================
# 生成飞书简报
# ============================================
generate_feishu_summary() {
    local commits_data="$1"
    local report_date="$2"
    local branches_list="$3"
    local authors_list="$4"
	# log_info " commits_data : $commits_data"
	# log_info " report_date : $report_date"
	# log_info " branches_list : $branches_list"
	# log_info " authors_list : $authors_list"

    local summary="📊 团队代码提交日报 (${REPORT_SINCE_DATE} 20:00 ~ ${REPORT_UNTIL_DATE} 20:00)

"

    if [ -z "$commits_data" ] || [ "$(echo "$commits_data" | grep -v '^$' | wc -l)" -eq 0 ]; then
        summary+="📭 今日暂无提交记录

跟踪分支: ${branches_list}"
        if [ -n "$authors_list" ]; then
            summary+="
统计人员: ${authors_list}"
        fi
        echo "$summary"
        return
    fi

    local total_commits=$(echo "$commits_data" | grep -v '^$' | wc -l)
    local total_authors=$(echo "$commits_data" | grep -v '^$' | cut -d'|' -f2 | sort -u | wc -l)
    local total_branches=$(echo "$commits_data" | grep -v '^$' | cut -d'|' -f6 | sort -u | wc -l)

    local bug_count=0
    local feat_count=0

    while IFS='|' read -r hash author date message stats branch; do
        [ -z "$message" ] && continue
        parsed=$(parse_commit_message "$message")
        type=$(echo "$parsed" | cut -d'|' -f1)
        case "$type" in
            bug) ((bug_count++)) ;;
            feature) ((feat_count++)) ;;
        esac
    done <<< "$commits_data"

    declare -A branch_summary
    while IFS='|' read -r hash author date message stats branch; do
        [ -z "$branch" ] && continue
        branch_summary["$branch"]=$((${branch_summary["$branch"]:-0} + 1))
    done <<< "$commits_data"

    # 统计AI提交
    declare -A author_ai_summary
    local total_ai_commits=0
    while IFS='|' read -r hash author date message stats branch; do
        [ -z "$author" ] && continue
        if is_ai_commit "$message"; then
            author_ai_summary["$author"]=$((${author_ai_summary["$author"]:-0} + 1))
            ((total_ai_commits++))
        fi
    done <<< "$commits_data"

    declare -A author_summary
    declare -A author_lines_added
    declare -A author_lines_removed
    while IFS='|' read -r hash author date message stats branch; do
        [ -z "$author" ] && continue
        author_summary["$author"]=$((${author_summary["$author"]:-0} + 1))
        
        # 统计代码行数
        if [ -n "$stats" ]; then
            local lines_add=$(echo "$stats" | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' | head -1 || echo "0")
            local lines_del=$(echo "$stats" | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' | head -1 || echo "0")
            [ -z "$lines_add" ] && lines_add=0
            [ -z "$lines_del" ] && lines_del=0
            author_lines_added["$author"]=$((${author_lines_added["$author"]:-0} + lines_add))
            author_lines_removed["$author"]=$((${author_lines_removed["$author"]:-0} + lines_del))
        fi
    done <<< "$commits_data"

    local ai_percent_summary=0
    if [ "$total_commits" -gt 0 ]; then
        ai_percent_summary=$((total_ai_commits * 100 / total_commits))
    fi

    summary+="📈 概览
• 总提交: ${total_commits} 次
• 参与人数: ${total_authors} 人
• 涉及分支: ${total_branches} 个
• Bug修复: ${bug_count} 个
• 功能开发: ${feat_count} 个
• AI提交: ${total_ai_commits} 次 (${ai_percent_summary}%)

🌿 分支统计
"

    for branch in "${!branch_summary[@]}"; do
        summary+="• ${branch}: ${branch_summary[$branch]} 次
"
    done

    summary+="
👥 个人提交 (提交数 | AI提交 | AI占比)
"

    # 获取每个作者的分支信息
    declare -A author_branches_summary
    while IFS='|' read -r hash author date message stats branch; do
        [ -z "$author" ] && continue
        [ -z "$branch" ] && continue
        local existing="${author_branches_summary[$author]}"
        if [[ ",$existing," != *",$branch,"* ]]; then
            if [ -z "$existing" ]; then
                author_branches_summary["$author"]="$branch"
            else
                author_branches_summary["$author"]="$existing,$branch"
            fi
        fi
    done <<< "$commits_data"

    for author in "${!author_summary[@]}"; do
        local count=${author_summary[$author]}
        local ai_count=${author_ai_summary["$author"]:-0}
        local ai_pct=0
        if [ "$count" -gt 0 ]; then
            ai_pct=$((ai_count * 100 / count))
        fi
        local branches="${author_branches_summary[$author]:-}"
        local lines_add=${author_lines_added["$author"]:-0}
        local lines_del=${author_lines_removed["$author"]:-0}
        summary+="• ${author}: ${count}次 | ${ai_count}次 | ${ai_pct}% | 分支:${branches} (+${lines_add}/-${lines_del})
"
    done

    summary+="
📄 详细报告已保存至 Obsidian"

    echo "$summary"
	# log_info "$summary"
}

# ============================================
# 保存到Obsidian
# ============================================
save_to_obsidian() {
    local content="$1"
    local date="$2"

    log_info "保存到 Obsidian..."

    # 保存到子目录: 05-日记/git-reports/
    local target_dir="${OBSIDIAN_VAULT_PATH}/${OBSIDIAN_DAILY_DIR}/${REPORT_SUBDIR}"
    local target_file="${target_dir}/git-commit-${date}.md"

    # 确保目录存在
    mkdir -p "$target_dir"

    # 写入文件
    echo "$content" > "$target_file"

    log_success "已保存到: $target_file"
    echo "$target_file"
}

# ============================================
# 主函数
# ============================================
main() {
    log_info "开始生成代码提交日报..."
    log_info "统计时间段: ${REPORT_SINCE_DATE} 20:00 ~ ${REPORT_UNTIL_DATE} 20:00"

    # 检查依赖
    check_dependencies

    # 获取配置（分支和人员）
    local config
    config=$(get_config 2>&1 | grep -v "^\[")
    BRANCHES=$(echo "$config" | grep '^BRANCHES:' | cut -d':' -f2-)
    AUTHORS=$(echo "$config" | grep '^AUTHORS:' | cut -d':' -f2-)

    log_info "跟踪分支: $BRANCHES"
    if [ -n "$AUTHORS" ]; then
        log_info "统计人员: $AUTHORS"
    else
        log_info "统计人员: 全部"
    fi

    # 获取所有分支的提交记录（昨天20:00到今天20:00）
    commits=$(get_all_commits "$REPORT_SINCE_DATE" "$REPORT_UNTIL_DATE" "$BRANCHES" "$AUTHORS")
    # log_info "commits : $commits"
    log_info "获取到 $(echo "$commits" | grep -v '^$' | wc -l) 条提交记录"
    # 生成报告（即使为空也生成）
    log_info "生成 Markdown 报告..."
    markdown_report=$(generate_markdown_report "$commits" "$REPORT_YESTERDAY" "$BRANCHES" "$AUTHORS")

    # 生成飞书简报
    log_info "生成飞书简报..."
    feishu_summary=$(generate_feishu_summary "$commits" "$REPORT_YESTERDAY" "$BRANCHES" "$AUTHORS")

    # 保存到Obsidian（使用日期范围作为文件名）
    obsidian_path=$(save_to_obsidian "$markdown_report" "${REPORT_SINCE_DATE}_20to${REPORT_UNTIL_DATE}_20")

    # 输出报告路径
    echo ""
    log_success "日报生成完成!"
    echo "Obsidian路径: $obsidian_path"

    # 输出飞书简报
    echo ""
    echo "=== FEISHU_SUMMARY_START ==="
    echo "$feishu_summary"
    echo "=== FEISHU_SUMMARY_END ==="
}

# 执行主函数
main
