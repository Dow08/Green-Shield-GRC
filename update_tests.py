import os
import glob
import re

for filepath in glob.glob('api/tests/**/*.py', recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = re.sub(
        r'monkeypatch\.setattr\(projects,\s*["\']PROJECTS_DIR["\'],\s*(.*?)\)',
        r'monkeypatch.setattr(projects, "PROJECTS_DIR", \1)\n    monkeypatch.setattr(projects.crud, "PROJECTS_DIR", \1)\n    monkeypatch.setattr(projects.exports, "PROJECTS_DIR", \1)\n    monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", \1)',
        content
    )

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
