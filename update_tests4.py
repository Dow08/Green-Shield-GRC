import os
import glob
import re

for filepath in glob.glob('api/tests/**/*.py', recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = re.sub(
        r'monkeypatch\.setattr\(projects\.crud,\s*["\']PROJECTS_DIR["\'],\s*(.*?)\)',
        r'monkeypatch.setattr(projects.crud, "PROJECTS_DIR", \1, raising=False)',
        content
    )
    new_content = re.sub(
        r'monkeypatch\.setattr\(projects\.exports,\s*["\']PROJECTS_DIR["\'],\s*(.*?)\)',
        r'monkeypatch.setattr(projects.exports, "PROJECTS_DIR", \1, raising=False)',
        new_content
    )
    new_content = re.sub(
        r'monkeypatch\.setattr\(projects\.snapshots_routes,\s*["\']PROJECTS_DIR["\'],\s*(.*?)\)',
        r'monkeypatch.setattr(projects.snapshots_routes, "PROJECTS_DIR", \1, raising=False)',
        new_content
    )

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
