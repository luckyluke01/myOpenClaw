#!/usr/bin/env python3
"""
Add a note to the personal notes Feishu document.
Usage: python add_note.py <type> <content> [doc_url]
Types: note, meeting, thinking
"""

import sys
import json
from datetime import datetime

def main():
    if len(sys.argv) < 3:
        print("Usage: python add_note.py <type> <content> [doc_url]", file=sys.stderr)
        sys.exit(1)
    
    note_type = sys.argv[1]
    content = sys.argv[2]
    doc_url = sys.argv[3] if len(sys.argv) > 3 else None
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Determine section and formatting based on type
    sections = {
        "note": ("## 📝 Daily Notes", f"**{timestamp}** — {content}"),
        "meeting": ("## 📅 Meetings", f"**{timestamp}**\n{content}\n- [ ] Follow-up required"),
        "thinking": ("## 💡 Thinking", f"**{timestamp}** — {content}"),
        "todo": ("## ✅ To-Do Items", f"**{timestamp}** — [ ] {content}")
    }
    
    section, formatted = sections.get(note_type, sections["note"])
    
    # Check if content indicates a pending issue (todo type is always pending)
    pending_keywords = ["问题", "待办", "todo", "待处理", "未完成", "pending"]
    is_pending = note_type == "todo" or any(kw in content for kw in pending_keywords)
    
    result = {
        "type": note_type,
        "section": section,
        "content": formatted,
        "timestamp": timestamp,
        "is_pending": is_pending,
        "doc_url": doc_url
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
