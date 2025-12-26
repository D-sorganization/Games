#!/usr/bin/env python3
"""
Script to automatically fix line length issues in the Force Field game files.
This will break long lines at appropriate points to comply with the 88 character limit.
"""

import re
import os

def fix_line_lengths(file_path, max_length=88):
    """Fix line length issues in a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for line_num, line in enumerate(lines, 1):
        if len(line.rstrip()) > max_length:
            # Handle common patterns that need line breaking
            fixed_line = fix_long_line(line)
            if fixed_line != line:
                print(f"Fixed line {line_num} in {file_path}")
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

def fix_long_line(line):
    """Fix a single long line by breaking it appropriately."""
    stripped = line.rstrip()
    indent = len(line) - len(line.lstrip())
    indent_str = line[:indent]
    
    # Handle pygame.draw.rect calls
    if 'pygame.draw.rect(' in stripped and 'border_radius=' in stripped:
        # Break before border_radius parameter
        pattern = r'(.*pygame\.draw\.rect\([^,]+,\s*[^,]+,\s*[^,]+),(\s*border_radius=.*)'
        match = re.match(pattern, stripped)
        if match:
            return match.group(1) + ',\n' + indent_str + '                         ' + match.group(2).strip() + '\n'
    
    # Handle pygame.draw.circle calls
    if 'pygame.draw.circle(' in stripped and len(stripped) > 88:
        # Break after the surface parameter
        pattern = r'(.*pygame\.draw\.circle\([^,]+,\s*[^,]+),(\s*.*)'
        match = re.match(pattern, stripped)
        if match:
            return match.group(1) + ',\n' + indent_str + '                             ' + match.group(2).strip() + '\n'
    
    # Handle pygame.draw.line calls
    if 'pygame.draw.line(' in stripped and len(stripped) > 88:
        # Break before the thickness parameter
        pattern = r'(.*pygame\.draw\.line\([^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+),(\s*.*)'
        match = re.match(pattern, stripped)
        if match:
            return match.group(1) + ',\n' + indent_str + '                           ' + match.group(2).strip() + '\n'
    
    # Handle screen.blit calls
    if 'screen.blit(' in stripped and len(stripped) > 88:
        # Break before the position parameter
        pattern = r'(.*screen\.blit\([^,]+),(\s*\(.*\).*)'
        match = re.match(pattern, stripped)
        if match:
            return match.group(1) + ',\n' + indent_str + '                      ' + match.group(2).strip() + '\n'
    
    # Handle tuple assignments that are too long
    if '=' in stripped and '(' in stripped and len(stripped) > 88:
        # Break long tuple assignments
        pattern = r'(\s*\w+\s*=\s*\([^,]+,\s*[^,]+),(\s*.*\))'
        match = re.match(pattern, stripped)
        if match:
            return match.group(1) + ',\n' + indent_str + '     ' + match.group(2).strip() + '\n'
    
    # If no specific pattern matched, try generic comma breaking
    if ',' in stripped and len(stripped) > 88:
        # Find a good place to break (after a comma, before 88 chars)
        for i in range(85, 40, -1):  # Work backwards from char 85
            if i < len(stripped) and stripped[i] == ',' and stripped[i+1] == ' ':
                part1 = stripped[:i+1]
                part2 = stripped[i+1:].strip()
                return part1 + '\n' + indent_str + '                         ' + part2 + '\n'
    
    return line

# Files to fix
files_to_fix = [
    'games/Force_Field/src/bot_renderer.py',
    'games/Force_Field/src/game.py',
    'games/Force_Field/src/renderer.py',
    'games/Force_Field/src/ui_renderer.py',
    'games/Force_Field/src/weapon_renderer.py'
]

if __name__ == '__main__':
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"Fixing line lengths in {file_path}...")
            fix_line_lengths(file_path)
        else:
            print(f"File not found: {file_path}")
    
    print("Line length fixes completed!")