import inspect
import sys

def patch_module_functions(module):
    """Patcher qui remplace les Depends(...) par leurs vraies valeurs quand les fonctions
    sont appelées directement dans les tests unitaires (sans passer par FastAPI/TestClient)."""
    for name, func in inspect.getmembers(module, inspect.isfunction):
        if name.startswith("_"):
            continue
        try:
            sig = inspect.signature(func)
        except Exception:
            continue
            
        has_depends = any(hasattr(p.default, 'dependency') or type(p.default).__name__ == 'Depends' for p in sig.parameters.values())
        if not has_depends:
            continue
            
        def make_wrapper(f, signature):
            def wrapper(*args, **kwargs):
                bound = signature.bind_partial(*args, **kwargs)
                bound.apply_defaults()
                created_sessions = []
                for k, v in bound.arguments.items():
                    if hasattr(v, 'dependency') or type(v).__name__ == 'Depends':
                        if k == 'db':
                            from modules.database.session import SessionLocal
                            s = SessionLocal()
                            bound.arguments[k] = s
                            created_sessions.append(s)
                        elif k == 'current_user':
                            from modules.database.models import User
                            bound.arguments[k] = User(id=0, email="test@test.local", role="user", is_premium=False)
                try:
                    return f(*bound.args, **bound.kwargs)
                finally:
                    for s in created_sessions:
                        try:
                            s.close()
                        except Exception:
                            pass
            return wrapper
            
        wrapped = make_wrapper(func, sig)
        setattr(module, name, wrapped)
        if "modules.projects" in sys.modules:
            setattr(sys.modules["modules.projects"], name, wrapped)
