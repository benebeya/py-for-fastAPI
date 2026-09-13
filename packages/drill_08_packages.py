"""DRILL 08 — MODULES, PACKAGES & LAYOUT   run: uv run packages/drill_08_packages.py
   There is a real package next to this file (shop/) that we import from."""
import sys
from pathlib import Path

# 1. MODULE = one .py | PACKAGE = a directory with __init__.py | SCRIPT = what you ran
#    Importing RUNS the module, top to bottom, exactly ONCE. Watch [executed] appear:
from shop.routers import products
print("1  importing again prints nothing — it's cached in sys.modules")
from shop.routers import products as again
print("1  same object:", products is again, "|", [m for m in sys.modules if m.startswith("shop")])

# 2. __init__.py defines the package's PUBLIC API. Keep it thin — anything heavy in
#    there runs on every import and is the usual source of circular imports.
import shop
from shop import Product            # short, thanks to a re-export in __init__.py
from shop.models import Product as P2   # long, always works
print("2  same class:", Product is P2, "| __all__:", shop.__all__, "| v", shop.__version__)

# 3. ABSOLUTE (shop/services/catalog.py):  from shop.config import settings
#    RELATIVE (shop/routers/products.py):  from ..models import Product
#      . = this package | .. = parent | ... = grandparent
#    Pick ONE style. Most FastAPI codebases use absolute.
print("3  both resolved:", products.index(), products.detail("wine"))
# Relative imports need package context: `python shop/routers/products.py` FAILS
# ("no known parent package"). Use `python -m shop.routers.products`.

# 4. sys.path[0] is the directory of the script you ran — that's why `import shop` works.
#    TRAP: your own file wins over the stdlib. A random.py / types.py / json.py in your
#    project silently breaks unrelated libraries. For real projects: uv pip install -e .
print("4  found shop at:", Path(shop.__file__).parent.name + "/__init__.py")

# 5. __name__ is "__main__" when RUN, "pkg.mod" when imported — the thing in your main.py
print("5  here:", __name__, "| imported:", products.__name__)
# So `if __name__ == "__main__":` = "only when run, not when imported". It's also how
# `uvicorn app.main:app` works: import app.main as a module, read the `app` attribute.

# 6. *** CIRCULAR IMPORTS *** — a imports b imports a. You WILL hit this.
try:
    import circular_a
except (ImportError, AttributeError) as e:
    print("6  failed ->", type(e).__name__, e)
# Importing A starts running A, which imports B, which imports A — half-built, so
# the NAME isn't there yet. (`import circular_b` often survives a cycle; it only
# needs the module object. `from circular_b import b_func` needs the name NOW.)
# In FastAPI it shows up as models <-> schemas, or routers <-> dependencies. Fixes:
#   (a) RESTRUCTURE so the dependency is one-directional  <- the real fix
#   (b) import INSIDE the function (deferred to call time)
#   (c) `if TYPE_CHECKING:` when you only need the name for a hint (free on 3.14)
sys.modules.pop("circular_a", None); sys.modules.pop("circular_b", None)

# 7. *** YOUR REPO ***  A module name must be a valid IDENTIFIER.
for n in ["Data structure ", "Async programming ", "type Hints", "args-kwargs"]:
    print(f"7  {n!r:22} importable? {n.isidentifier()}")
# You can RUN those files but never `import` from them. Fine for practice scripts,
# fatal for an app. Use: data_structures/ async_programming/ type_hints/ args_kwargs/

# 8. THE LAYOUT TO USE.  Dependency direction, left to right — never backwards:
#      config <- database <- models <- services <- routers <- main
#    app/__init__.py  main.py (FastAPI() + include_router)  config.py (Settings)
#       database.py (engine, SessionLocal, get_db)  dependencies.py
#       models/    <- SQLAlchemy tables  (what the DB stores)
#       schemas/   <- Pydantic models    (what the API accepts/returns)
#       routers/   <- one APIRouter per resource
#       services/  <- business logic, imports no FastAPI
#    tests/  alembic/  pyproject.toml  .env(gitignored)
#    Keeping models/ and schemas/ apart is what stops you leaking password hashes.
#    uv add "sqlalchemy>=2.0" alembic aiosqlite; uv add --dev pytest httpx
#    uv run uvicorn app.main:app --reload

# ===================== EXERCISES =====================
# E1 add shop/services/pricing.py with total_value() -> int; import it from catalog.py
#    without creating a cycle, then call it here
# E2 re-export get_product from shop/__init__.py so `from shop import get_product`
#    works. Does that create a cycle? Why not?
# E3 fix circular_a/circular_b with fix (b), then: assert circular_a.a_func() == "a -> b"
# E4 fix the SAME pair with fix (a) instead — extract circular_shared.py. Which is better?
# E5 rename your four broken folders (use `git mv`) + add __init__.py, so this works:
#    from data_structures import drill_01_collections
# E6 build the section-8 skeleton for real under my-api/; confirm `uv run python -c
#    "import app.main"` works
