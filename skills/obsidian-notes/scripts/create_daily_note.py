#!/usr/bin/env python3
"""
Create a daily note with template for Obsidian.
"""

import argparse
from datetime import datetime
from pathlib import Path

def create_daily_note_template(date_str: str, vault_path: str) -> str:
    """Create a daily note template."""
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    weekday = date_obj.strftime('%A')
    
    template = f"""---
date: {date_str}
day: {weekday}
type: daily
---

# {date_str} ({weekday})

## 🎯 Today's Focus


## 📝 Notes


## ✅ Tasks

- [ ] 

## 💡 Ideas & Thoughts


## 🔗 Related
- [[00-MOC]]
- [[{date_str}]]

## 📊 Daily Reflection
- What went well?
- What could be better?
- What to remember?

---
*Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    return template

def create_daily_note(vault_path: str, date: str = None):
    """Create daily note for given date (default: today)."""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    vault = Path(vault_path)
    daily_folder = vault / "05-日记"
    daily_folder.mkdir(parents=True, exist_ok=True)
    
    note_path = daily_folder / f"{date}.md"
    
    if note_path.exists():
        print(f"Note already exists: {note_path}")
        return str(note_path)
    
    template = create_daily_note_template(date, vault_path)
    note_path.write_text(template, encoding='utf-8')
    
    print(f"✓ Created daily note: {note_path}")
    return str(note_path)

def main():
    parser = argparse.ArgumentParser(description='Create daily note for Obsidian')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--date', help='Date (YYYY-MM-DD), defaults to today')
    
    args = parser.parse_args()
    
    create_daily_note(args.vault, args.date)

if __name__ == '__main__':
    main()
