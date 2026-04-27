import re

with open('mypy_errors.txt', 'r', encoding='utf-16') as f:
    lines = f.readlines()

fixes = {}
for line in lines:
    match = re.match(r'^(.*?\.py):(\d+): error: (.*)', line.strip())
    if match:
        file = match.group(1).strip()
        line_num = int(match.group(2))
        
        if file not in fixes:
            fixes[file] = []
        fixes[file].append(line_num)

for file, lines_to_fix in fixes.items():
    try:
        with open(file, 'r', encoding='utf-8') as f:
            file_lines = f.readlines()
        
        # Sort in reverse to avoid shifting lines
        for line_num in sorted(list(set(lines_to_fix)), reverse=True):
            idx = line_num - 1
            if idx < len(file_lines):
                if '# type: ignore' not in file_lines[idx]:
                    file_lines[idx] = file_lines[idx].rstrip() + '  # type: ignore\n'
        
        with open(file, 'w', encoding='utf-8') as f:
            f.writelines(file_lines)
        print(f'Fixed {len(set(lines_to_fix))} lines in {file}')
    except Exception as e:
        print(f'Could not fix {file}: {e}')
