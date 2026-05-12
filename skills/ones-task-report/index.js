const axios = require('axios');

// 配置
const CONFIG = {
  apiUrl: 'https://gitee.ibr.net.cn/forge/api/search',
  headers: {
    'X-Parse-Application-Id': 'Bonree',
    'X-Parse-Session-Token': 'a:74aee1a75660146be9c2aaf4',
    'Content-Type': 'application/json'
  },
  fields: ['createdBy', 'field019', 'key', 'workspace', 'name', 'itemType', 'field002'],
  pageSize: 200
};

// 解析日期
function parseDateRange(startDate, endDate) {
  const start = startDate || getWeekRange('current').start;
  const end = endDate || getWeekRange('current').end;
  return { start, end };
}

function getWeekRange(type) {
  const now = new Date();
  const dayOfWeek = now.getDay();
  const diff = now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
  
  const monday = new Date(now.setDate(diff));
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  
  const format = d => d.toISOString().split('T')[0];
  
  if (type === 'current') {
    return { start: format(monday), end: format(sunday) };
  } else {
    const prevMonday = new Date(monday);
    prevMonday.setDate(monday.getDate() - 7);
    const prevSunday = new Date(prevMonday);
    prevSunday.setDate(prevMonday.getDate() + 6);
    return { start: format(prevMonday), end: format(prevSunday) };
  }
}

// 获取所有数据（分页）
async function fetchAllTasks(startDate, endDate) {
  const { start, end } = parseDateRange(startDate, endDate);
  
  const iql = `('实际完成时间' >= '${start}' and '实际完成时间' <= '${end}' and '负责人' in ["membersOf(数据底座能力部)"]) order by 创建时间 desc`;
  
  let allItems = [];
  let from = 0;
  let hasMore = true;
  
  while (hasMore) {
    const response = await axios.post(CONFIG.apiUrl, {
      iql,
      size: CONFIG.pageSize,
      from,
      execFieldBehaviors: true,
      fields: CONFIG.fields
    }, { headers: CONFIG.headers });
    
    const data = response.data;
    if (data.code === 0 && data.payload) {
      const items = data.payload.items || [];
      allItems = allItems.concat(items);
      
      if (items.length < CONFIG.pageSize) {
        hasMore = false;
      } else {
        from += CONFIG.pageSize;
      }
    } else {
      throw new Error(data.message || 'API请求失败');
    }
  }
  
  return { items: allItems, start, end };
}

// 提取字段信息
function extractFields(items) {
  return items.map(item => {
    const createdBy = item.createdBy?.nickname || item.createdBy?.username || '未知';
    const workHours = item.values?.field019 || 0;
    const key = item.key || '';
    const workspace = item.workspace?.name || item.workspace?.key || '';
    const name = item.name || '';
    const type = item.itemType?.name || '未知类型';
    const description = item.field002 || '';
    
    return { key, name, type, createdBy, workspace, workHours, description };
  });
}

// 分类统计
function categorizeTasks(tasks) {
  const stats = {
    byType: {},
    byCategory: {},
    byPerson: {},
    totalHours: 0
  };
  
  for (const task of tasks) {
    // 按类型统计
    if (!stats.byType[task.type]) {
      stats.byType[task.type] = { count: 0, hours: 0 };
    }
    stats.byType[task.type].count++;
    stats.byType[task.type].hours += task.workHours;
    
    // 按人员统计
    if (!stats.byPerson[task.createdBy]) {
      stats.byPerson[task.createdBy] = { count: 0, hours: 0 };
    }
    stats.byPerson[task.createdBy].count++;
    stats.byPerson[task.createdBy].hours += task.workHours;
    
    // 按业务方向分类（从任务标题提取）
    const category = extractCategory(task.name, task.description);
    if (!stats.byCategory[category]) {
      stats.byCategory[category] = { count: 0, hours: 0 };
    }
    stats.byCategory[category].count++;
    stats.byCategory[category].hours += task.workHours;
    
    stats.totalHours += task.workHours;
  }
  
  return stats;
}

// 从任务标题/描述提取业务方向
function extractCategory(name, description) {
  const text = (name + ' ' + (description || '')).toLowerCase();
  
  if (text.includes('case') || text.includes('缺陷') || text.includes('bug')) {
    return 'Case/缺陷处理';
  } else if (text.includes('titan-client')) {
    return 'Titan-Client';
  } else if (text.includes('titan-query') || text.includes('queryservice')) {
    return 'Titan-Query';
  } else if (text.includes('ck-manager') || text.includes('ckmanager')) {
    return 'CK-Manager';
  } else if (text.includes('meeting') || text.includes('会议')) {
    return '会议/沟通';
  } else if (text.includes('压测') || text.includes('性能')) {
    return '性能测试';
  } else if (text.includes('血缘')) {
    return '数据血缘';
  } else if (text.includes('meta') || text.includes('元数据')) {
    return '元数据';
  } else if (text.includes('测试') || text.includes('验证')) {
    return '测试/验证';
  } else {
    return '其他';
  }
}

// 格式化输出
function formatOutput(tasks, stats, startDate, endDate) {
  let output = `# ONES 任务工时统计\n`;
  output += `**统计周期**: ${startDate} ~ ${endDate}\n`;
  output += `**任务总数**: ${tasks.length}\n`;
  output += `**总工时**: ${stats.totalHours.toFixed(1)} 小时\n\n`;
  
  // 任务明细表格
  output += `## 任务明细\n\n`;
  output += `| 序号 | 任务编号 | 任务标题 | 类型 | 负责人 | 工时 |\n`;
  output += `| --- | --- | --- | --- | --- | --- |\n`;
  
  tasks.forEach((task, idx) => {
    const title = task.name.length > 30 ? task.name.substring(0, 30) + '...' : task.name;
    output += `| ${idx + 1} | ${task.key} | ${title} | ${task.type} | ${task.createdBy} | ${task.workHours} |\n`;
  });
  
  output += `\n## 按业务方向统计\n\n`;
  output += `| 业务方向 | 任务数 | 工时 | 占比 |\n`;
  output += `| --- | --- | --- | --- |\n`;
  
  const sortedCategories = Object.entries(stats.byCategory)
    .sort((a, b) => b[1].hours - a[1].hours);
  
  for (const [category, data] of sortedCategories) {
    const percent = ((data.hours / stats.totalHours) * 100).toFixed(1);
    output += `| ${category} | ${data.count} | ${data.hours.toFixed(1)} | ${percent}% |\n`;
  }
  
  output += `\n## 按任务类型统计\n\n`;
  output += `| 任务类型 | 任务数 | 工时 | 占比 |\n`;
  output += `| --- | --- | --- | --- |\n`;
  
  const sortedTypes = Object.entries(stats.byType)
    .sort((a, b) => b[1].hours - a[1].hours);
  
  for (const [type, data] of sortedTypes) {
    const percent = ((data.hours / stats.totalHours) * 100).toFixed(1);
    output += `| ${type} | ${data.count} | ${data.hours.toFixed(1)} | ${percent}% |\n`;
  }
  
  output += `\n## 按人员统计\n\n`;
  output += `| 人员 | 任务数 | 工时 | 占比 |\n`;
  output += `| --- | --- | --- | --- |\n`;
  
  const sortedPersons = Object.entries(stats.byPerson)
    .sort((a, b) => b[1].hours - a[1].hours);
  
  for (const [person, data] of sortedPersons) {
    const percent = ((data.hours / stats.totalHours) * 100).toFixed(1);
    output += `| ${person} | ${data.count} | ${data.hours.toFixed(1)} | ${percent}% |\n`;
  }
  
  return output;
}

// 主函数
async function main(args) {
  let startDate = null;
  let endDate = null;
  
  if (args.includes('本周')) {
    const range = getWeekRange('current');
    startDate = range.start;
    endDate = range.end;
  } else if (args.includes('上周')) {
    const range = getWeekRange('previous');
    startDate = range.start;
    endDate = range.end;
  } else {
    // 尝试解析日期参数
    for (let i = 0; i < args.length; i++) {
      if (args[i].match(/^\d{4}-\d{2}-\d{2}$/)) {
        if (!startDate) startDate = args[i];
        else endDate = args[i];
      }
    }
  }
  
  console.log('正在获取数据...');
  const { items, start, end } = await fetchAllTasks(startDate, endDate);
  
  console.log(`获取到 ${items.length} 条任务记录`);
  
  const tasks = extractFields(items);
  const stats = categorizeTasks(tasks);
  
  const output = formatOutput(tasks, stats, start, end);
  console.log(output);
  
  return output;
}

// 导出
module.exports = { main, fetchAllTasks, extractFields, categorizeTasks };

// 直接运行
if (require.main === module) {
  main(process.argv.slice(2)).catch(console.error);
}
