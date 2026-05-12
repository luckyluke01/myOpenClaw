#!/usr/bin/env python3
"""
Sync todos from Feishu document to Obsidian daily notes.
Creates or appends to YYYY-MM-DD.md in the Daily folder.
"""

import argparse
import re
import os
from datetime import datetime
from pathlib import Path

# Feishu doc API would be imported here in real implementation
# For now, this is a template that reads from local cache or manual input

def parse_feishu_content(content: str) -> list[dict]:
    """Parse Feishu document content to extract todos."""
    todos = []
    
    # Pattern: YYYY-MM-DD HH:MM — [ ] task description
    # or: YYYY-MM-DD HH:MM — task description
    pattern = r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+—\s+(?:\[\s*\]\s+)?(.+)'
    
    for match in re.finditer(pattern, content):
        date_str, time_str, task = match.groups()
        todos.append({
            'date': date_str,
            'time': time_str,
            'task': task.strip(),
            'completed': '[x]' in task or '✓' in task
        })
    
    return todos

def get_daily_note_path(vault_path: str, date: str) -> Path:
    """Get path to daily note for a given date."""
    daily_folder = Path(vault_path) / "05-日记"
    daily_folder.mkdir(parents=True, exist_ok=True)
    return daily_folder / f"{date}.md"

def create_daily_note_template(date: str) -> str:
    """Create template for a new daily note."""
    return f"""---
date: {date}
type: daily
---

# {date}

## 📝 Notes from Feishu

"""

def sync_todos_to_obsidian(vault_path: str, feishu_content: str, target_date: str = None):
    """Sync todos from Feishu to Obsidian daily notes."""
    todos = parse_feishu_content(feishu_content)
    
    if target_date:
        todos = [t for t in todos if t['date'] == target_date]
    
    # Group todos by date
    todos_by_date = {}
    for todo in todos:
        if todo['date'] not in todos_by_date:
            todos_by_date[todo['date']] = []
        todos_by_date[todo['date']].append(todo)
    
    for date, date_todos in todos_by_date.items():
        note_path = get_daily_note_path(vault_path, date)
        
        if note_path.exists():
            content = note_path.read_text(encoding='utf-8')
        else:
            content = create_daily_note_template(date)
        
        # Add todos
        new_entries = []
        for todo in date_todos:
            if not todo['completed']:
                new_entries.append(f"- [ ] {todo['time']} - {todo['task']}")
        
        if new_entries:
            content += '\n'.join(new_entries) + '\n'
            note_path.write_text(content, encoding='utf-8')
            print(f"✓ Added {len(new_entries)} todos to {note_path}")

def main():
    parser = argparse.ArgumentParser(description='Sync Feishu todos to Obsidian')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--content', required=True, help='Feishu document content')
    parser.add_argument('--date', help='Target date (YYYY-MM-DD), defaults to all dates')
    
    args = parser.parse_args()
    
    sync_todos_to_obsidian(args.vault, args.content, args.date)

if __name__ == '__main__':
    main()
