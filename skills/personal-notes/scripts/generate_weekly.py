#!/usr/bin/env python3
"""
Generate weekly summary from notes.
Usage: python generate_weekly.py <doc_content> [week_start_date]
"""

import sys
import json
import re
from datetime import datetime, timedelta

def parse_notes(content):
    """Parse document content into categorized notes."""
    notes = {
        "general": [],
        "meetings": [],
        "thinking": [],
        "pending": []
    }
    
    lines = content.split('\n')
    current_section = None
    
    for line in lines:
        if '📝 Daily Notes' in line:
            current_section = 'general'
        elif '📅 Meetings' in line:
            current_section = 'meetings'
        elif '💡 Thinking' in line:
            current_section = 'thinking'
        elif current_section and line.strip() and not line.startswith('#'):
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if date_match:
                note = {
                    "date": date_match.group(1),
                    "content": line.strip(),
                    "is_pending": any(m in line for m in ['[ ]', '☐', '待办', 'TODO'])
                }
                notes[current_section].append(note)
                if note["is_pending"]:
                    notes["pending"].append(note)
    
    return notes

def generate_summary(notes, week_start=None):
    """Generate weekly summary."""
    if week_start is None:
        week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
    
    summary = {
        "week_range": f"{week_start} ~ {week_end}",
        "generated_at": datetime.now().isoformat(),
        "total_notes": len(notes["general"]),
        "total_meetings": len(notes["meetings"]),
        "total_thinking": len(notes["thinking"]),
        "pending_count": len(notes["pending"]),
        "sections": {
            "meetings": [n["content"] for n in notes["meetings"]],
            "thinking": [n["content"] for n in notes["thinking"]],
            "pending": [n["content"] for n in notes["pending"]]
        }
    }
    
    return summary

def format_report(summary):
    """Format summary as readable text."""
    report = f"""# 📊 Weekly Summary ({summary['week_range']})

Generated at: {summary['generated_at'][:10]}

## 📈 Statistics
- General Notes: {summary['total_notes']}
- Meetings: {summary['total_meetings']}
- Ideas/Thoughts: {summary['total_thinking']}
- Pending Issues: {summary['pending_count']}

## 📅 Meetings
"""
    
    if summary['sections']['meetings']:
        for item in summary['sections']['meetings'][-5:]:  # Last 5 meetings
            report += f"- {item}\n"
    else:
        report += "_No meetings recorded_\n"
    
    report += "\n## 💡 Key Ideas\n"
    if summary['sections']['thinking']:
        for item in summary['sections']['thinking'][-5:]:
            report += f"- {item}\n"
    else:
        report += "_No ideas recorded_\n"
    
    report += "\n## ⚠️ Pending Issues\n"
    if summary['sections']['pending']:
        for item in summary['sections']['pending']:
            report += f"- [ ] {item}\n"
    else:
        report += "_No pending issues_\n"
    
    return report

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_weekly.py '<doc_content>' [week_start_date]", file=sys.stderr)
        sys.exit(1)
    
    content = sys.argv[1]
    week_start = sys.argv[2] if len(sys.argv) > 2 else None
    
    notes = parse_notes(content)
    summary = generate_summary(notes, week_start)
    report = format_report(summary)
    
    result = {
        "summary": summary,
        "report": report
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
