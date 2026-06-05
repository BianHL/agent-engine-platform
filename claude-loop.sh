#!/bin/bash
# ==============================================================================
#  Claude Loop - 无人值守自动化执行脚本
#  版本: 2.1.0
#  用途: 使用 claude -p 命令循环执行 prompt 任务，支持无人值守运行
# ==============================================================================

set -o pipefail

# ==============================================================================
# 配置区（请根据需要修改）
# ==============================================================================
PROMPT_SOURCE="file"                    # "file" | "string"
PROMPT_FILE=".claude/prompt/prompt.md"               # 文件模式时：prompt 文件路径
PROMPT_STRING=""                        # 字符串模式时：直接输入 prompt 内容

MAX_ITERATIONS=0                        # 0 = 无限循环，N = 执行 N 次后停止
SLEEP_INTERVAL=30                       # 每次执行间隔（秒）
LOG_DIR=".claude/logs"                        # 日志目录
LOG_FILE="$LOG_DIR/claude-loop.log"     # 主日志文件路径（仅记录执行状态）
ERROR_LOG="$LOG_DIR/claude-loop-error.log" # 错误日志文件路径
MAX_RETRIES=3                           # 单次任务失败时的最大重试次数
LOG_MAX_SIZE=$((100 * 1024 * 1024))     # 日志文件最大大小（100MB），超过则轮转

# 上下文传递配置（将前一次的"后续建议"注入到下一次执行）
ENABLE_CONTEXT_PASSING=1                        # 1=启用, 0=禁用
SUGGESTIONS_MARKER="## 后续建议"                 # Claude 输出中后续建议的标记（请与 prompt 中要求的格式一致）
CONTEXT_MAX_LENGTH=8000                         # 上下文最大长度（字符），防止 prompt 过长

# Claude 命令额外参数
CLAUDE_FLAGS=(
    "--permission-mode" "bypassPermissions"
    "--output-format" "text"
)

# ==============================================================================
# 内部变量（请勿修改）
# ==============================================================================
SCRIPT_NAME="$(basename "$0")"
TERMINATE_FLAG=0
ITERATION=0
FIRST_RUN=1

# 动态生成状态文件路径（基于日志目录）
STATE_DIR="$LOG_DIR/.state"
CONTEXT_FILE="$STATE_DIR/context.md"
LAST_OUTPUT_FILE="$STATE_DIR/last-output.md"
SESSION_ID_FILE="$STATE_DIR/session-id"

# ==============================================================================
# 工具函数
# ==============================================================================

# 确保目录存在，不存在则创建
ensure_dir() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir" 2>/dev/null || {
            echo "[ERROR] 无法创建目录: $dir" >&2
            exit 1
        }
    fi
}

# ==============================================================================
# 日志函数
# ==============================================================================
log_info() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

log_error() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1"
    echo "$msg" >&2
    echo "$msg" >> "$LOG_FILE"
    echo "$msg" >> "$ERROR_LOG"
}

log_warn() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

# ==============================================================================
# 从 Claude 输出中提取"后续建议"
# ==============================================================================
extract_suggestions() {
    local input_file="$1"
    local output_file="$2"

    if [[ ! -f "$input_file" ]]; then
        return 1
    fi

    # 查找标记，提取标记所在行到文件末尾（使用 awk 避免 sed 兼容性问题）
    if grep -q "$SUGGESTIONS_MARKER" "$input_file"; then
        awk -v marker="$SUGGESTIONS_MARKER" '
            $0 ~ marker { found=1 }
            found { print }
        ' "$input_file" > "$output_file"
        return 0
    fi

    return 1
}

# ==============================================================================
# 构建带上下文的完整 prompt
# ==============================================================================
build_prompt() {
    local base_prompt="$1"

    # 如果禁用上下文传递，或没有历史上下文，直接返回原始 prompt
    if [[ "$ENABLE_CONTEXT_PASSING" -ne 1 ]]; then
        echo "$base_prompt"
        return 0
    fi

    if [[ ! -f "$CONTEXT_FILE" ]]; then
        echo "$base_prompt"
        return 0
    fi

    local context_content
    context_content=$(cat "$CONTEXT_FILE")

    if [[ -z "$context_content" ]]; then
        echo "$base_prompt"
        return 0
    fi

    # 截断过长的上下文
    local original_length=${#context_content}
    if [[ "$original_length" -gt "$CONTEXT_MAX_LENGTH" ]]; then
        context_content="${context_content:0:$CONTEXT_MAX_LENGTH}..."
        log_warn "上下文内容已从 $original_length 字符截断至 $CONTEXT_MAX_LENGTH 字符"
    fi

    # 优化衔接：让上下文作为补充参考自然融入，而非生硬分隔
    local full_prompt
    full_prompt="${base_prompt}

---
【上下文参考：前一次任务执行结束后，Claude 提出了以下后续建议】
请在本次执行中参考并落实这些建议：

${context_content}
---"

    echo "$full_prompt"
}

# ==============================================================================
# 日志轮转：当日志超过 LOG_MAX_SIZE 时自动重命名备份
# ==============================================================================
rotate_log_if_needed() {
    local logfile="$1"
    if [[ ! -f "$logfile" ]]; then
        return 0
    fi

    local size
    if command -v stat >/dev/null 2>&1; then
        # macOS stat
        size=$(stat -f%z "$logfile" 2>/dev/null || echo 0)
    fi

    if [[ -z "$size" || "$size" -eq 0 ]]; then
        # Linux stat fallback
        size=$(stat -c%s "$logfile" 2>/dev/null || echo 0)
    fi

    if [[ "$size" -gt "$LOG_MAX_SIZE" ]]; then
        local backup="${logfile}.$(date '+%Y%m%d_%H%M%S')"
        mv "$logfile" "$backup"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] 日志轮转: $logfile -> $backup" >> "$logfile"
    fi
}

# ==============================================================================
# 信号处理：优雅退出
# ==============================================================================
cleanup() {
    log_info "接收到终止信号，正在优雅退出... (当前迭代: $ITERATION)"
    TERMINATE_FLAG=1
}

trap cleanup SIGINT SIGTERM

# ==============================================================================
# 环境检查
# ==============================================================================
check_environment() {
    # 检查 claude 命令
    if ! command -v claude >/dev/null 2>&1; then
        echo "[ERROR] claude 命令未找到，请确保 Claude Code CLI 已安装并添加到 PATH" >&2
        exit 1
    fi

    # 检查 prompt 来源
    if [[ "$PROMPT_SOURCE" == "file" ]]; then
        if [[ -z "$PROMPT_FILE" ]]; then
            echo "[ERROR] PROMPT_SOURCE=file 但 PROMPT_FILE 未设置" >&2
            exit 1
        fi
        if [[ ! -f "$PROMPT_FILE" ]]; then
            echo "[ERROR] Prompt 文件不存在: $PROMPT_FILE" >&2
            exit 1
        fi
    elif [[ "$PROMPT_SOURCE" == "string" ]]; then
        if [[ -z "$PROMPT_STRING" ]]; then
            echo "[ERROR] PROMPT_SOURCE=string 但 PROMPT_STRING 为空" >&2
            exit 1
        fi
    else
        echo "[ERROR] PROMPT_SOURCE 必须是 'file' 或 'string'" >&2
        exit 1
    fi

    # 确保所有需要的目录存在
    ensure_dir "$LOG_DIR"
    ensure_dir "$STATE_DIR"
}

# ==============================================================================
# 执行 Claude 任务（带重试 + 上下文传递）
# ==============================================================================
run_claude_task() {
    local base_prompt=""

    if [[ "$PROMPT_SOURCE" == "file" ]]; then
        base_prompt=$(cat "$PROMPT_FILE")
    else
        base_prompt="$PROMPT_STRING"
    fi

    # 构建带上下文的完整 prompt，并在最前面固定添加 skill 调用
    local full_prompt
    full_prompt=$(build_prompt "$base_prompt")
    full_prompt="/superpowers:using-superpowers

${full_prompt}"

    local attempt=1
    while [[ $attempt -le $MAX_RETRIES ]]; do
        log_info "开始执行 (尝试 $attempt/$MAX_RETRIES)"

        # 构建本次执行的 claude flags
        local claude_flags=("${CLAUDE_FLAGS[@]}")

        if [[ "$FIRST_RUN" -eq 1 ]]; then
            # 第一次执行：使用固定的 session-id 创建新会话
            local session_id
            if [[ -f "$SESSION_ID_FILE" ]]; then
                session_id=$(cat "$SESSION_ID_FILE")
                log_info "使用已有 Session ID: $session_id"
            else
                session_id=$(uuidgen)
                ensure_dir "$STATE_DIR"
                echo "$session_id" > "$SESSION_ID_FILE"
                log_info "创建新 Session ID: $session_id"
            fi
            claude_flags+=("--session-id" "$session_id")
            FIRST_RUN=0
        else
            # 后续执行：使用 --continue 延续同一会话
            claude_flags+=("--continue")
            log_info "延续上一次会话 (--continue)"
        fi

        # 执行 claude -p 命令
        # 输出仅保存到 LAST_OUTPUT_FILE，不写入主日志
        local output_file
        output_file=$(mktemp)

        claude -p "${claude_flags[@]}" "$full_prompt" > "$output_file" 2>&1
        local exit_code=$?

        if [[ $exit_code -eq 0 ]]; then
            log_info "任务执行成功 (尝试 $attempt/$MAX_RETRIES)"

            # 保存完整输出到状态文件
            ensure_dir "$STATE_DIR"
            cp "$output_file" "$LAST_OUTPUT_FILE"
            log_info "完整输出已保存到: $LAST_OUTPUT_FILE"

            # 提取后续建议
            if [[ "$ENABLE_CONTEXT_PASSING" -eq 1 ]]; then
                if extract_suggestions "$output_file" "$CONTEXT_FILE"; then
                    log_info "已提取后续建议（$(wc -c < "$CONTEXT_FILE" | tr -d ' ') 字符），将注入到下一次执行"
                else
                    log_warn "未在输出中找到后续建议标记: $SUGGESTIONS_MARKER"
                fi
            fi

            rm -f "$output_file"
            return 0
        else
            rm -f "$output_file"

            # 检查是否收到终止信号
            if [[ $TERMINATE_FLAG -eq 1 ]]; then
                log_info "收到终止信号，停止重试"
                return 1
            fi

            log_error "任务执行失败 (尝试 $attempt/$MAX_RETRIES, 退出码: $exit_code)"
            attempt=$((attempt + 1))

            if [[ $attempt -le $MAX_RETRIES ]]; then
                log_warn "将在 5 秒后重试..."
                sleep 5
            fi
        fi
    done

    log_error "任务最终失败，已重试 $MAX_RETRIES 次，进入下一次循环"
    return 1
}

# ==============================================================================
# 主循环
# ==============================================================================
main() {
    check_environment

    log_info "========================================"
    log_info "Claude Loop 启动"
    log_info "版本: 2.1.0"
    log_info "模式: $( [[ "$MAX_ITERATIONS" -eq 0 ]] && echo "无限循环" || echo "最多 $MAX_ITERATIONS 次" )"
    log_info "间隔: ${SLEEP_INTERVAL}秒"
    log_info "Prompt 来源: $PROMPT_SOURCE"
    if [[ "$PROMPT_SOURCE" == "file" ]]; then
        log_info "Prompt 文件: $PROMPT_FILE"
    fi
    if [[ "$ENABLE_CONTEXT_PASSING" -eq 1 ]]; then
        log_info "上下文传递: 已启用 (标记: $SUGGESTIONS_MARKER)"
    else
        log_info "上下文传递: 已禁用"
    fi
    log_info "日志目录: $LOG_DIR"
    log_info "状态目录: $STATE_DIR"
    log_info "========================================"

    while true; do
        # 检查终止信号
        if [[ $TERMINATE_FLAG -eq 1 ]]; then
            break
        fi

        ITERATION=$((ITERATION + 1))

        # 检查是否达到最大迭代次数
        if [[ $MAX_ITERATIONS -gt 0 && $ITERATION -gt $MAX_ITERATIONS ]]; then
            log_info "已达到最大迭代次数 ($MAX_ITERATIONS)，脚本正常结束"
            break
        fi

        log_info "===== 第 $ITERATION 次执行 ====="

        # 日志轮转检查
        rotate_log_if_needed "$LOG_FILE"
        rotate_log_if_needed "$ERROR_LOG"

        # 执行核心任务
        run_claude_task

        # 检查终止信号（任务执行期间可能收到）
        if [[ $TERMINATE_FLAG -eq 1 ]]; then
            break
        fi

        # 休眠
        log_info "本次执行完成，休眠 ${SLEEP_INTERVAL} 秒"
        sleep "$SLEEP_INTERVAL"
    done

    log_info "========================================"
    log_info "Claude Loop 结束，共执行 $ITERATION 次"
    log_info "========================================"
}

# ==============================================================================
# 入口
# ==============================================================================
main "$@"
