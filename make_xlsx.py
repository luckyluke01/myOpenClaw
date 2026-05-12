import zipfile
import csv
import re
from io import StringIO, BytesIO

# Read the categories.json file
import json
with open('/mnt/e/chromedoanload/allure-report/allure-report/data/categories.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract failed test cases
failed_cases = []

for category in data.get('children', []):
    category_name = category.get('name', '')
    for defect in category.get('children', []):
        defect_name = defect.get('name', '')
        
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
                'error_message': defect_name,
                'category': category_name,
                'status': status
            })

print(f"Total failed cases: {len(failed_cases)}")

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
    
    # xl/styles.xml
    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b><sz val="11"/><name val="Calibri"/></b><color rgb="FFFFFFFF"/></font></fonts>
<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFD9D9D9"/><bgColor rgb="FFD9D9D9"/></patternFill></fill></fills>
<borders count="1"><border/></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="1" borderId="0" xfId="0" applyFont="1" applyFill="1"/><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" wrapText="1"/></cellXfs>
</styleSheet>'''
    zf.writestr('xl/styles.xml', styles)
    
    # xl/worksheets/sheet1.xml
    # Build rows
    rows = []
    # Header row
    headers = ['序号', 'UID', '测试名称', '指标名称', '函数', '维度', '错误信息', '分类', '状态']
    row_xml = '<row r="1">'
    for idx, h in enumerate(headers, 1):
        row_xml += f'<c r="{chr(64+idx)}1" t="inlineStr" s="1"><is><t>{xml_escape(h)}</t></is></c>'
    row_xml += '</row>'
    rows.append(row_xml)
    
    # Data rows
    for row_idx, case in enumerate(failed_cases, 2):
        row_xml = f'<row r="{row_idx}">'
        values = [
            str(row_idx-1),
            case['uid'],
            case['test_name'],
            case['metric_name'],
            case['function'],
            case['dimensions'],
            case['error_message'],
            case['category'],
            case['status']
        ]
        for col_idx, val in enumerate(values, 1):
            col_letter = chr(64+col_idx) if col_idx <= 26 else chr(64+(col_idx//26)) + chr(64+(col_idx%26))
            row_xml += f'<c r="{col_letter}{row_idx}" t="inlineStr"><is><t>{xml_escape(val)}</t></is></c>'
        row_xml += '</row>'
        rows.append(row_xml)
    
    sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<cols>
<col min="1" max="1" width="8" customWidth="1"/>
<col min="2" max="2" width="20" customWidth="1"/>
<col min="3" max="3" width="30" customWidth="1"/>
<col min="4" max="4" width="45" customWidth="1"/>
<col min="5" max="5" width="12" customWidth="1"/>
<col min="6" max="6" width="60" customWidth="1"/>
<col min="7" max="7" width="80" customWidth="1"/>
<col min="8" max="8" width="15" customWidth="1"/>
<col min="9" max="9" width="10" customWidth="1"/>
</cols>
<sheetData>
{''.join(rows)}
</sheetData>
</worksheet>'''
    zf.writestr('xl/worksheets/sheet1.xml', sheet_xml)

# Save
output_path = '/mnt/f/.openclaw/workspace/失败用例清单.xlsx'
with open(output_path, 'wb') as f:
    f.write(output.getvalue())

print(f"Excel file saved to: {output_path}")
