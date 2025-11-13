from django.db import connection, reset_queries
from functools import wraps
import time

def debug_queries(func):
    """Mide las queries ejecutadas por una función."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        reset_queries()
        t0 = time.time()
        result = func(*args, **kwargs)
        total = len(connection.queries)
        elapsed = time.time() - t0
        if total:
            print(f"\n⚙️ {func.__qualname__} ejecutó {total} queries en {elapsed:.3f}s")
            for q in connection.queries[:5]:  # Mostramos solo las primeras
                print("  ", q['sql'])
        else:
            print(f"\n✅ {func.__qualname__} no ejecutó queries ({elapsed:.3f}s)")
        return result
    return wrapper
