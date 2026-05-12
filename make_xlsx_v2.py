import zipfile
import json
import re
from io import BytesIO

# Read the categories.json file
with open('/mnt/e/chromedoanload/allure-report/allure-report/data/categories.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract failed test cases with dimension and category extraction
failed_cases = []

for category in data.get('children', []):
    category_name = category.get('name', '')
    for defect in category.get('children', []):
        defect_name = defect.get('name', '')
        
        # Extract dimension from error message
        dimension_match = re.search(r'dimension \[([^\]]+)\]', defect_name)
        dimension = dimension_match.group(1) if dimension_match else ''
        
        # Classify error into larger categories
        error_lower = defect_name.lower()
        if 'dimension' in error_lower and 'not exist' in error_lower:
            error_type = '维度不存在'
        elif 'syntax error' in error_lower:
            error_type = 'SQL语法错误'
        elif 'datatype is blank' in error_lower:
            error_type = '数据类型为空'
        elif 'missing columns' in error_lower:
            error_type = '列不存在'
        elif 'there is no supertype' in error_lower:
            error_type = '类型不兼容'
        elif 'extractrowsdata error' in error_lower:
            error_type = '数据类型转换失败'
        elif 'parseSQL' in error_lower or '解析' in error_lower:
            error_type = 'SQL解析失败'
        else:
            error_type = '其他错误'
        
        for test_case in defect.get('children', []):
            test_name = test_case.get('name', '')
            uid = test_case.get('uid', '')
            status = test_case.get('status', '')
            parameters = test_case.get('parameters', [])
            
            metric_name = parameters[0] if len(parameters) > 0 else ''
            function = parameters[1] if len(parameters) > 1 else ''
            dimensions = parameters[4] if len(parameters) > 4 else ''
            
            failed_cases.append({
                'uid': uid,
                'test_name': test_name,
                'metric_name': metric_name,
                'function': function,
                'dimensions': dimensions,
                'dimension_from_error': dimension,
                'error_type': error_type,
                'error_message': defect_name,
                'category': category_name,
                'status': status
            })

print(f"Total failed cases: {len(failed_cases)}")

# Count by error type
error_type_counts = {}
for case in failed_cases:
    et = case['error_type']
    error_type_counts[et] = error_type_counts.get(et, 0) + 1

print("\nError type distribution:")
for et, count in sorted(error_type_counts.items(), key=lambda x: -x[1]):
    print(f"  {et}: {count}")

# Escape XML special characters
def xml_escape(s):
    if s is None:
        return ''
    s = str(s)
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    s = s.replace("'", '&apos;')
    return s

# Build XLSX as ZIP with XML
output = BytesIO()
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
    # [Content_Types].xml
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>'''
    zf.writestr('[Content_Types].xml', content_types)
    
    # _rels/.rels
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''
    zf.writestr('_rels/.rels', rels)
    
    # xl/workbook.xml
    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="失败用例清单" sheetId="1" r:id="rId1"/></sheets>
</workbook>'''
    zf.writestr('xl/workbook.xml', workbook)
    
    # xl/_rels/workbook.xml.rels
    workbook_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''
    zf.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
    
    # xl/styles.xml - header with blue background
    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b><sz val="11"/><name val="Calibri"/></b></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF4472C4"/><bgColor rgb="FF4472C4"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor="FFFF0000"/></patternFill></fills>
<borders count="1"><border/></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="4"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="1" borderId="0" xfId="0" applyFont="1" applyFill="1"/><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" wrapText="1"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>
</styleSheet>'''
    zf.writestr('xl/styles.xml', styles)
    
    # xl/worksheets/sheet1.xml
    rows = []
    # Header row - style 1 (blue background, bold)
    headers = ['序号', 'UID', '测试名称', '指标名称', '函数', '维度', '错误维度', '错误大类', '错误信息', '分类', '状态']
    row_xml = '<row r="1">'
    for idx, h in enumerate(headers, 1):
        col_letter = chr(64+idx) if idx <= 26 else 'A' + chr(64+idx-26)
        row_xml += f'<c r="{col_letter}1" t="inlineStr" s="1"><is><t>{xml_escape(h)}</t></is></c>'
    row_xml += '</row>'
    rows.append(row_xml)
    
    # Data rows - style 2 (wrap text)
    for row_idx, case in enumerate(failed_cases, 2):
        row_xml = f'<row r="{row_idx}">'
        values = [
            str(row_idx-1),
            case['uid'],
            case['test_name'],
            case['metric_name'],
            case['function'],
            case['dimensions'],
            case['dimension_from_error'],
            case['error_type'],
            case['error_message'],
            case['category'],
            case['status']
        ]
        for col_idx, val in enumerate(values, 1):
            col_letter = chr(64+col_idx) if col_idx <= 26 else 'A' + chr(64+col_idx-26)
            row_xml += f'<c r="{col_letter}{row_idx}" t="inlineStr" s="2"><is><t>{xml_escape(val)}</t></is></c>'
        row_xml += '</row>'
        rows.append(row_xml)
    
    sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<cols>
<col min="1" max="1" width="8" customWidth="1"/>
<col min="2" max="2" width="20" customWidth="1"/>
<col min="3" max="3" width="30" customWidth="1"/>
<col min="4" max="4" width="45" customWidth="1"/>
<col min="5" max="5" width="10" customWidth="1"/>
<col min="6" max="6" width="60" customWidth="1"/>
<col min="7" max="7" width="25" customWidth="1"/>
<col min="8" max="8" width="18" customWidth="1"/>
<col min="9" max="9" width="100" customWidth="1"/>
<col min="10" max="10" width="15" customWidth="1"/>
<col min="11" max="11" width="10" customWidth="1"/>
</cols>
<sheetData>
{''.join(rows)}
</sheetData>
</worksheet>'''
    zf.writestr('xl/worksheets/sheet1.xml', sheet_xml)

# Save
output_path = '/mnt/f/.openclaw/workspace/失败用例清单_增强版.xlsx'
with open(output_path, 'wb') as f:
    f.write(output.getvalue())

print(f"\nExcel file saved to: {output_path}")
