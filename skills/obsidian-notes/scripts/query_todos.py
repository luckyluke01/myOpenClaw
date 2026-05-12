#!/usr/bin/env python3
"""
Query all pending todos from Obsidian vault.
Searches for - [ ] patterns across all markdown files.
"""

import argparse
import re
from pathlib import Path
from datetime import datetime

def find_todos_in_file(file_path: Path) -> list[dict]:
    """Extract todos from a markdown file."""
    todos = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return todos
    
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Match: - [ ] todo text
        match = re.match(r'^(\s*)-\s\[\s*\]\s+(.+)$', line)
        if match:
            indent, task = match.groups()
            todos.append({
                'file': file_path.name,
                'path': str(file_path),
                'line': line_num,
                'task': task.strip(),
                'indent_level': len(indent) // 2
            })
    
    return todos

def query_all_todos(vault_path: str) -> dict:
    """Query all pending todos from vault."""
    vault = Path(vault_path)
    all_todos = {
        'daily': [],
        'projects': [],
        'areas': [],
        'other': []
    }
    
    for md_file in vault.rglob('*.md'):
        todos = find_todos_in_file(md_file)
        
        for todo in todos:
            path_str = str(md_file.relative_to(vault))
            
            if '05-日记' in path_str or '日记' in path_str:
                all_todos['daily'].append(todo)
            elif '01-项目' in path_str or '项目' in path_str:
                all_todos['projects'].append(todo)
            elif '02-领域' in path_str or '领域' in path_str:
                all_todos['areas'].append(todo)
            else:
                all_todos['other'].append(todo)
    
    return all_todos

def print_todos(todos: dict):
    """Print todos in a formatted way."""
    total = sum(len(v) for v in todos.values())
    print(f"\n📋 Found {total} pending todos\n")
    
    categories = [
        ('Projects', 'projects', '🔥'),
        ('Areas', 'areas', '📌'),
        ('Daily Notes', 'daily', '📝'),
        ('Other', 'other', '📎')
    ]
    
    for name, key, emoji in categories:
        items = todos.get(key, [])
        if items:
            print(f"{emoji} {name} ({len(items)}):")
            for todo in items:
                indent = "  " * todo['indent_level']
                print(f"  {indent}• {todo['task']} ({todo['file']})")
            print()

def export_todos_to_markdown(todos: dict, output_path: str):
    """Export todos to a markdown file for review."""
    output = Path(output_path)
    
    lines = [
        f"# Pending Todos - {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"**Total:** {sum(len(v) for v in todos.values())} pending items",
        ""
    ]
    
    categories = [
        ('Projects', 'projects'),
        ('Areas', 'areas'),
        ('Daily Notes', 'daily'),
        ('Other', 'other')
    ]
    
    for name, key in categories:
        items = todos.get(key, [])
        if items:
            lines.extend([f"## {name}", ""])
            for todo in items:
                lines.append(f"- [ ] {todo['task']} ({todo['file']})")
            lines.append("")
    
    output.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✓ Exported to {output}")

def main():
    parser = argparse.ArgumentParser(description='Query pending todos from Obsidian vault')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--export', help='Export to markdown file')
    
    args = parser.parse_args()
    
    todos = query_all_todos(args.vault)
    print_todos(todos)
    
    if args.export:
        export_todos_to_markdown(todos, args.export)

if __name__ == '__main__':
    main()
