import ast

with open('api/modules/projects/crud.py', 'r', encoding='utf-8') as f:
    source = f.read()

tree = ast.parse(source)

# Let's find all functions decorated with @router.xxx
routes = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        is_route = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if hasattr(dec.func.value, 'id') and dec.func.value.id == 'router':
                    is_route = True
        if is_route:
            routes.append(node.name)

print("Routes found:", routes)
