#!/usr/bin/env python3
"""
Comprehensive script to fix all line length issues in the Force Field game files.
"""

import re
import subprocess
import sys

def run_ruff_check():
    """Get current ruff errors."""
    result = subprocess.run(['ruff', 'check', 'games/Force_Field/src/', '--output-format=concise'], 
                          capture_output=True, text=True)
    return result.stdout.strip().split('\n') if result.stdout.strip() else []

def fix_file_line_lengths(file_path):
    """Fix line length issues in a specific file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Common patterns to fix
    fixes = [
        # pygame.draw.rect with border_radius
        (r'(pygame\.draw\.rect\([^,]+,\s*[^,]+,\s*[^,]+),(\s*border_radius=[^)]+\))', 
         r'\1,\n                         \2'),
        
        # pygame.draw.circle with long parameters
        (r'(pygame\.draw\.circle\([^,]+,\s*[^,]+),(\s*\([^)]+\),\s*[^)]+\))', 
         r'\1,\n                             \2'),
        
        # screen.blit with long parameters
        (r'(screen\.blit\([^,]+),(\s*\([^)]+\))', 
         r'\1,\n                      \2'),
        
        # Long tuple assignments
        (r'(\s+\w+\s*=\s*\([^,]+,\s*[^,]+,\s*[^,]+),(\s*[^)]+\))', 
         r'\1,\n\2'),
        
        # Long function calls with multiple parameters
        (r'(\w+\([^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+),(\s*[^)]+\))', 
         r'\1,\n                           \2'),
    ]
    
    original_content = content
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed line lengths in {file_path}")
        return True
    return False

def main():
    files_to_fix = [
        'games/Force_Field/src/bot_renderer.py',
        'games/Force_Field/src/game.py', 
        'games/Force_Field/src/renderer.py',
        'games/Force_Field/src/ui_renderer.py',
        'games/Force_Field/src/weapon_renderer.py'
    ]
    
    print("Fixing line length issues...")
    
    for file_path in files_to_fix:
        try:
            fix_file_line_lengths(file_path)
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
    
    # Check remaining errors
    errors = run_ruff_check()
    print(f"\nRemaining errors: {len([e for e in errors if e.strip()])}")
    
    if errors and errors[0]:
        print("Remaining line length errors:")
        for error in errors[:10]:  # Show first 10
            if 'E501' in error:
                print(f"  {error}")

if __name__ == '__main__':
    main()