#!/usr/bin/env python3
"""
Extract pending issues from notes document.
Usage: python get_pending.py <doc_content>
"""

import sys
import json
import re
from datetime import datetime

def extract_pending_issues(content):
    """Extract lines marked as pending/todo."""
    pending = []
    lines = content.split('\n')
    
    for line in lines:
        # Check for todo markers or pending keywords
        if any(marker in line for marker in ['[ ]', '☐', '待办', 'TODO', '问题']):
            # Extract date if present
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            date = date_match.group(1) if date_match else 'Unknown'
            
            # Clean up the line
            clean_line = re.sub(r'\[\s*\]|☐|TODO|todo|待办', '', line).strip()
            if clean_line and len(clean_line) > 5:
                pending.append({
                    "date": date,
                    "content": clean_line,
                    "raw": line.strip()
                })
    
    return pending

def main():
    if len(sys.argv) < 2:
        print("Usage: python get_pending.py '<doc_content>'", file=sys.stderr)
        sys.exit(1)
    
    content = sys.argv[1]
    pending = extract_pending_issues(content)
    
    result = {
        "count": len(pending),
        "pending": pending,
        "generated_at": datetime.now().isoformat()
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
