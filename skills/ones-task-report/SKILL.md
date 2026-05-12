# ONES 任务工时统计 Skill

从 ONES 系统获取任务工时数据，进行汇总统计和分析。

## 配置

在 `config.json` 中配置以下参数：

```json
{
  "api_url": "https://gitee.ibr.net.cn/forge/api/search",
  "headers": {
    "X-Parse-Application-Id": "Bonree",
    "X-Parse-Session-Token": "your-session-token",
    "Content-Type": "application/json"
  },
  "iql_template": "('实际完成时间' >= '{start_date}' and '实际完成时间' <= '{end_date}' and '负责人' in [\"membersOf(数据底座能力部)\"]) order by 创建时间 desc",
  "fields": [
    "createdBy",
    "field019", 
    "key",
    "workspace",
    "name",
    "itemType",
    "field002"
  ],
  "page_size": 200
}
```

## 使用方式

### 获取指定日期范围的任务工时

```
/ones工时 2026-03-09 2026-03-15
```

### 统计本周工时

```
/ones工时 本周
```

### 统计上周工时

```
/ones工时 上周
```

## 输出格式

1. **任务明细表格** - 包含任务编号、标题、类型、负责人、已登记工时
2. **工时统计** - 按任务类型/业务方向分类统计人力投入占比

## 依赖

需要 Node.js 环境，安装依赖：
```bash
npm install axios
```
