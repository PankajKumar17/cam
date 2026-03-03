import os
import re

directory = r'c:\Users\panka\OneDrive\Desktop\hackathon'

replacements = {
    'Intelli-Credit': 'Yakṣarāja',
    'intelli-credit': 'yaksaraja',
    'INTELLI-CREDIT': 'YAKṢARĀJA',
    'Intelli-credit': 'Yakṣarāja'
}

exclude_dirs = {'.git', '.pytest_cache', 'venv', 'env', '__pycache__', 'node_modules'}
exclude_exts = {'.pyc', '.png', '.jpg', '.pdf', '.xlsx', '.docx'}

for root, dirs, files in os.walk(directory):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if any(file.endswith(ext) for ext in exclude_exts):
            continue
        filepath = os.path.join(root, file)
        if file == 'tmp_replace.py': continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception:
                continue
                
        new_content = content
        for old, new in replacements.items():
            new_content = new_content.replace(old, new)
            
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
