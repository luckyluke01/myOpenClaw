# 长期记忆

## 2026年5月

### 5月14日下午
- 心跳检查: 待办 12个（进行中，无变化）
- MEMORY.md 例行更新

### 5月13日下午/晚间
- CK query error report 脚本: `run.sh` → `run.py` (修复 subprocess body 截断 bug)
- Bug: `subprocess.run(capture_output=True)` + `stdout.rsplit()` 导致 HTTP status 200 被误认为 body，body 截断为 `'200'`
- 修复: 改用 `Popen.communicate()` + `decode('utf-8', errors='replace')` 正确提取 JSON body
- 修复后报表正常生成: 总错误 1518 次(TYPE_MISMATCH 95.5%), 错误率 0.01%, 25 个涉及时段
- 样例查询字段调整: `exception_message` → `type` (列名不存在)

### 5月13日凌晨
- 心跳检查: 待办 12个（进行中，无变化）
- MEMORY.md 例行更新
- CK query error report 脚本 bug 修复: `subprocess.run` + `capture_output=True` 改为 `subprocess.Popen` + `communicate()` + `decode('utf-8', errors='replace')`，解决了 body 提取被截断为 `'200'` 的问题
- 报告新增: 完整 SQL + type 字段（exception_message 列不存在），按错误类型分组展示 Top3 样例 + 根因分析
- 近24小时统计结果: 1518次错误，TYPE_MISMATCH(53) 占95.5%，NO_COMMON_TYPE(386) 占4.1%

### 5月13日下午
- 待办事项: 12个（进行中，无变化）
- 新增待办: 记录模型是否可以跟日志模型合并的讨论与设计

### 5月12日晚间
- CK query error report 脚本重构: `run.sh` → `run.py` (解决 shell 转义问题)
- 报告新增: 完整 SQL + exception (不缩略)、Top3 错误类型样例、错误原因总结章节
- 根因提取逻辑: 正则匹配 TYPE_MISMATCH/UNKNOWN_IDENTIFIER/NO_COMMON_TYPE 等错误模式
- git-commit-tracker (5/11~5/12): 71次提交，55人参与，AI提交11次(15%)
- Bug修复: 2个, 功能开发: 18个
- 提交排名: 杨宪亮(14次,57%AI), 张翔(3次,0%AI), 王睿(2次,100%AI), 王俊(1次,100%AI)

### 5月12日下午
- 待办事项: 12个（进行中，无变化）
- 新增待办: 记录模型是否可以跟日志模型合并的讨论与设计

### 5月11日上午
- 心跳检查: 待办 11个（进行中，无变化）
- git-commit-tracker (5/10~5/11): 7次提交，7人参与，AI提交0次(0%)
- MEMORY.md 例行更新

### 5月9日晚间
- git-commit-tracker: 102次提交，93人参与，AI提交9次(8%)
- 提交排名: 王俊(5次,100%AI), 张翔(4次,0%AI), 王浩(2次,50%AI), 邢雪杰(2次,100%AI), 郭全德(1次,100%AI)
- 功能开发: 11个, Bug修复: 3个

### 5月6日
- git-commit-tracker: Cron 触发但脚本目录 `/mnt/f/.openclaw/workspace/git-commit-tracker` 不存在（之前已记录），实际路径为 `scripts/git-commit-tracker/run.sh`
- 发票统计: Luke 桌面 `C:\Users\hi\Desktop\发票\202604` 下 23 个文件，按文件名 `-` 前数字统计，总金额 ¥11,375.00
- 待办事项: 11个（进行中，无变化）
- MEMORY.md 例行更新

## 2026年4月

### 4月29日晚间
- git-commit-tracker: 165次提交，108人参与，AI提交30次(18%)
- 提交排名: 王宏旭(21次,23%AI), 王俊(15次,100%AI), 王浩(8次,25%AI), 邢雪杰(6次,66%AI), 王明超(6次,0%AI), 郭全德(5次,40%AI), 王睿(2次,50%AI), 张翔(2次,50%AI), 陈雪兵(1次,0%AI)
- 功能开发: 52个, Bug修复: 14个

### 4月30日
- 心跳检查: 待办 11个（进行中，无变化）

### 4月25日
- git-commit-tracker: 182次提交，98人参与，AI提交68次(37%)
- 提交排名: 冯庆雨(45次,62%AI), 邢雪杰(18次,100%AI), 王俊(9次,100%AI), 杨龙伟(7次,100%AI), 王浩(4次,0%AI), 郭全德(3次,33%AI), 杨宪亮(3次,33%AI), 王宏旭(2次,100%AI), 张翔(2次,100%AI)

## 重要信息

### 系统配置
- 时间: Asia/Shanghai (GMT+8)
- 工作目录: /mnt/f/.openclaw/workspace
- Obsidian vault: \mnt\F\obsidion\lukeguo
- git-commit-tracker 脚本路径: `scripts/git-commit-tracker/run.sh`（原 `git-commit-tracker/run.sh` 路径不存在）

### Cron 任务
1. obsidian-git-commit - 每天 20:00
2. git-commit-tracker-daily - 每天 20:00
3. 每日待办提醒 - 每天 21:00
4. obsidian-auto-commit - 每天 00:00
5. 每周周报生成 - 每周日 20:00

### 用户
- 姓名: Luke
- 飞书用户: ou_bccc4ada608b8339a67f9426c7e03301
