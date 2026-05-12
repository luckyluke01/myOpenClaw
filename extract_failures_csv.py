import json
import csv

# Read the categories.json file
with open('/mnt/e/chromedoanload/allure-report/allure-report/data/categories.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract failed test cases
failed_cases = []

# Process Product defects category
for category in data.get('children', []):
    category_name = category.get('name', '')
    for defect in category.get('children', []):
        defect_name = defect.get('name', '')
        
        # Extract error message from defect name
        error_msg = defect_name
        
        for test_case in defect.get('children', []):
            test_name = test_case.get('name', '')
            uid = test_case.get('uid', '')
            status = test_case.get('status', '')
            parameters = test_case.get('parameters', [])
            
            # Extract metric name, function, dimensions from parameters
            metric_name = parameters[0] if len(parameters) > 0 else ''
            function = parameters[1] if len(parameters) > 1 else ''
            dimensions = parameters[4] if len(parameters) > 4 else ''
            
            failed_cases.append({
                'uid': uid,
                'test_name': test_name,
                'metric_name': metric_name,
                'function': function,
                'dimensions': dimensions,
                'error_message': error_msg,
                'category': category_name,
                'status': status
            })

print(f"Total failed cases: {len(failed_cases)}")

# Write CSV
output_path = '/mnt/f/.openclaw/workspace/失败用例清单.csv'
with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    # Headers
    writer.writerow(['序号', 'UID', '测试名称', '指标名称', '函数', '维度', '错误信息', '分类', '状态'])
    
    # Data
    for idx, case in enumerate(failed_cases, 1):
        writer.writerow([
            idx,
            case['uid'],
            case['test_name'],
            case['metric_name'],
            case['function'],
            case['dimensions'],
            case['error_message'],
            case['category'],
            case['status']
        ])

print(f"CSV file saved to: {output_path}")
