import ast

with open('api/modules/projects/crud.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('api/modules/projects/crud.py', 'r', encoding='utf-8') as f:
    source = f.read()

tree = ast.parse(source)

exports_funcs = [
    'export_project_archive',
    'export_project_html', 'export_project_html_synthese', 'export_project_html_tableau', 
    'export_project_html_registre', 'export_project_html_cartographie',
    'export_project_docx', 'export_project_nda_docx', 'export_project_ebios_docx', 
    'export_project_pssi_docx', 'export_project_aipd_docx', 'export_project_soa_docx', 
    'export_project_document'
]

snapshots_funcs = [
    'list_snapshots', 'restore_snapshot'
]

crud_drop = exports_funcs + snapshots_funcs

def extract_funcs(drop_names):
    keep_lines = [True] * len(lines)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name in drop_names:
                # drop from decorators to end of function
                start = node.lineno - 1
                if node.decorator_list:
                    start = node.decorator_list[0].lineno - 1
                end = node.end_lineno
                for i in range(start, end):
                    keep_lines[i] = False
    return "".join(lines[i] for i, k in enumerate(keep_lines) if k)

crud_content = extract_funcs(crud_drop)
with open('api/modules/projects/crud.py', 'w', encoding='utf-8') as f:
    f.write(crud_content)

# For exports, we drop everything that is a route but NOT an export
all_routes = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        is_route = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if hasattr(dec.func.value, 'id') and dec.func.value.id == 'router':
                    is_route = True
        if is_route:
            all_routes.append(node.name)

export_drop = [r for r in all_routes if r not in exports_funcs]
export_content = extract_funcs(export_drop)
with open('api/modules/projects/exports.py', 'w', encoding='utf-8') as f:
    f.write(export_content)

snapshot_drop = [r for r in all_routes if r not in snapshots_funcs]
snapshot_content = extract_funcs(snapshot_drop)
with open('api/modules/projects/snapshots_routes.py', 'w', encoding='utf-8') as f:
    f.write(snapshot_content)
