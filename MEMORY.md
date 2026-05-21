# 长期记忆

## 2026年5月

### 5月21日早间
- 心跳检查: 待办 12个（进行中，无变化）

### 5月20日凌晨
- 心跳检查: 待办 12个（进行中，无变化）
- MEMORY.md 例行更新

### 5月19日晚间
- 心跳检查: 待办 12个（进行中，无变化）

### 5月18日
- CK 错误报表任务失败 (2026-05-18 21:05)：`run.py` 在解析汇总数据时崩溃，原因是 API 返回 code:500 错误（`"Code: 202. DB::..."`），`result` 字段为字符串而非字典。需要修复 `run.py`，在解析 JSON 后检查 `code` 字段是否为 200，若非 200 则记录错误并退出。

### 5月17日晚间
- 心跳检查: 待办 12个（进行中，无变化）

### 5月17日下午
- 心跳检查: 待办 12个（进行中，无变化）

### 5月17日傍晚
- 心跳检查: 待办 12个（中行改代码4个，港交所灾备4个，MOC 2个），无变化

### 5月17日早间
- 心跳检查: 待办 12个（进行中，无变化）

### 5月16日晚间
- git-commit-tracker (5/15~5/16): 0次提交，无数据
- 待办 12个（进行中，无变化）

### 5月16日早间
- 心跳检查: 待办 10个（中行改代码4个，港交所灾备4个，MOC 2个），无变化

### 5月15日晚间
- git-commit-tracker (5/14~5/15): 86次提交，74人参与，AI提交8次(9%)
- 提交排名: 王明超(4次), 王俊(3次,100%AI), 王浩(2次,100%AI), 张翔(6次,33%AI)
- Bug修复: 5个, 功能开发: 13个
- 报告路径: `05-日记/git-reports/git-commit-2026-05-14_20to2026-05-15_20.md`

### 5月13日凌晨
- CK query error report 脚本 bug 修复: `subprocess.run` + `capture_output=True` 改为 `subprocess.Popen` + `communicate()` + `decode('utf-8', errors='replace')`，解决了 body 提取被截断为 `'200'` 的问题
- 报告新增: 完整 SQL + type 字段（exception_message 列不存在），按错误类型分组展示 Top3 样例 + 根因分析
- 近24小时统计结果: 1518次错误，TYPE_MISMATCH(53) 占95.5%，NO_COMMON_TYPE(386) 占4.1%

### 5月13日下午
- 待办事项: 12个（进行中，无变化）
- 新增待办: 记录模型是否可以跟日志模型合并的讨论与设计

### 5月12日晚间
- CK query error report 脚本重构: `run.sh` → `run.py` (解决 shell 转义问题)
- 报告新增: 完整 SQL + exception (不缩略)、Top3 错误类型样例、错误原因总结章节
- git-commit-tracker (5/11~5/12): 71次提交，55人参与，AI提交11次(15%)

### 5月11日上午
- git-commit-tracker (5/10~5/11): 7次提交，7人参与，AI提交0次(0%)

### 5月9日晚间
- git-commit-tracker: 102次提交，93人参与，AI提交9次(8%)

### 5月6日
- 发票统计: Luke 桌面 `C:\Users\hi\Desktop\发票\202604` 下 23 个文件，总金额 ¥11,375.00

### 4月29日晚间
- git-commit-tracker: 165次提交，108人参与，AI提交30次(18%)
- 提交排名: 王宏旭(21次,23%AI), 王俊(15次,100%AI), 王浩(8次,25%AI), 邢雪杰(6次,66%AI)

### 4月25日
- git-commit-tracker: 182次提交，98人参与，AI提交68次(37%)

## 重要信息

### 系统配置
- 时间: Asia/Shanghai (GMT+8)
- 工作目录: /mnt/f/.openclaw/workspace
- Obsidian vault: \mnt\F\obsidion\lukeguo
- git-commit-tracker 脚本路径: `scripts/git-commit-tracker/run.sh`

### Cron 任务
1. obsidian-git-commit - 每天 20:00
2. git-commit-tracker-daily - 每天 20:00
3. 每日待办提醒 - 每天 21:00
4. obsidian-auto-commit - 每天 00:00
5. 每周周报生成 - 每周日 20:00

### 用户
- 姓名: Luke
- 飞书用户: ou_bccc4ada608b8339a67f9426c7e03301