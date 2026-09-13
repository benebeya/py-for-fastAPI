"""
DRILL 08 — MODULES, PACKAGES & PROJECT LAYOUT

The last prerequisite. Everything so far was one file at a time; a FastAPI
app never is. This is also the drill that fixes a concrete problem in your
repo — see §8.

There is a real package next to this file (`shop/`) that we import from.

Run it:  uv run packages/drill_08_packages.py
"""

import sys
import types
from pathlib import Path


# ==========================================================================
# 1. THE THREE WORDS
# ==========================================================================
# MODULE  — one .py file.
# PACKAGE — a directory of modules, with an __init__.py.
# SCRIPT  — whatever file you actually ran. It gets the name "__main__".
#
# Importing a module RUNS it, top to bottom, exactly once. Watch the
# [executed] lines appear as we import — and note they do NOT repeat.

print("1.1  importing shop.routers.products ...")
from shop.routers import products

print("1.2  importing it again (no output — already cached):")
from shop.routers import products as products_again
print("1.3  same module object:", products is products_again)
print("1.4  the cache:", [m for m in sys.modules if m.startswith("shop")])

# sys.modules is why import side effects happen once. It's also why editing a
# module mid-session doesn't take effect without a restart.


# ==========================================================================
# 2. WHAT __init__.py IS FOR
# ==========================================================================
import shop

print("2.1  package version:", shop.__version__)
print("2.2  re-exported:", shop.Product("wine", 500))
print("2.3  package __path__:", Path(shop.__path__[0]).name)

# shop/__init__.py did `from shop.models import Product`, so callers get the
# short spelling. Compare:
from shop import Product              # short — thanks to __init__
from shop.models import Product as P2 # long — always works
print("2.4  same class:", Product is P2)

# Keep __init__.py small. Anything expensive in there runs on every import of
# anything inside the package, and it's the usual source of circular imports.


# ==========================================================================
# 3. ABSOLUTE vs RELATIVE IMPORTS
# ==========================================================================
# ABSOLUTE (shop/services/catalog.py):
#     from shop.config import settings
#     from shop.models import Product
#
# RELATIVE (shop/routers/products.py):
#     from ..models import Product
#     from ..services.catalog import get_product
#
#   .   = current package
#   ..  = parent package
#   ... = grandparent
#
# Absolute is explicit and greppable; relative is short and rename-proof.
# Pick ONE and use it everywhere. Most FastAPI codebases use absolute.

print("3.1  both styles resolved fine:", products.index())
print("3.2  detail():", products.detail("wine"))

# The catch with relative imports: they need package context. Running
# `python shop/routers/products.py` directly fails with
# "attempted relative import with no known parent package", because as a
# script it has no parent. Use `python -m shop.routers.products` instead.


# ==========================================================================
# 4. HOW PYTHON FINDS THINGS — sys.path
# ==========================================================================
# Import searches sys.path in order. Entry 0 is the directory of the script
# you ran, which is why `import shop` works here at all.

print("4.1  sys.path[0]:", Path(sys.path[0]).name or "<cwd>")
print("4.2  entries:", len(sys.path))
print("4.3  shop found at:", Path(shop.__file__).parent.name + "/__init__.py")

# THE SHADOWING TRAP: your own file wins over the stdlib. A file named
# random.py, types.py, email.py or json.py in your project directory will
# break unrelated libraries in a very confusing way.
print("4.4  stdlib `types` came from:", Path(types.__file__).parent.name)
# If that ever prints your project folder, you have a shadowing bug.

# For a real project, don't touch sys.path. Install the project instead:
#     uv pip install -e .          # editable install
# then `from app.routers import users` works from anywhere.


# ==========================================================================
# 5. __name__ — the thing in your main.py
# ==========================================================================
print("5.1  this file's __name__:", __name__)            # __main__
print("5.2  an imported module's:", products.__name__)   # shop.routers.products

# So:
#     if __name__ == "__main__":
#         main()
# means "only when this file was RUN, not when it was imported."
# Without it, importing your module would start your server.
#
# This is also how uvicorn finds your app: `uvicorn app.main:app` imports
# app/main.py as a module (not as __main__) and reads the `app` variable.


# ==========================================================================
# 6. __all__ AND STAR IMPORTS
# ==========================================================================
print("6.1  shop.__all__:", shop.__all__)
# `from shop import *` imports exactly those names. Without __all__, it grabs
# every name not starting with an underscore — usually including things you
# never meant to export.
#
# Define __all__ in your packages. Then never use `import *` anyway: it makes
# code unreadable and hides shadowing.


# ==========================================================================
# 7. *** CIRCULAR IMPORTS *** — you WILL hit this in FastAPI
# ==========================================================================
# circular_a imports circular_b, which imports circular_a. Boom.

try:
    import circular_a
    print("7.1  unexpected: it worked")
except (ImportError, AttributeError) as e:
    print("7.1  circular import failed ->", type(e).__name__, e)

# Why: importing A starts running A, which imports B, which imports A —
# but A is only half-built, so the name B wants isn't there yet.
#
# In FastAPI this shows up as models <-> schemas, or routers <-> dependencies.
#
# THREE FIXES, best first:
#
# (a) RESTRUCTURE — the real fix. Make the dependency one-directional.
#     Extract the shared piece into a third module both can import.
#     That's why shop/config.py imports nothing: it's a leaf.
#
# (b) IMPORT INSIDE THE FUNCTION — deferred until call time, by which point
#     both modules are fully loaded:
#
#         def a_func():
#             import circular_b          # not at module level
#             return circular_b.b_func()
#
# (c) TYPE-CHECKING-ONLY IMPORT — when you only need the name for a hint.
#     On 3.14 annotations are lazy (Drill 02 §11), so this costs nothing:
#
#         from typing import TYPE_CHECKING
#         if TYPE_CHECKING:
#             from shop.models import Product
#
#         def get() -> "Product": ...

sys.modules.pop("circular_a", None)
sys.modules.pop("circular_b", None)


# ==========================================================================
# 8. *** THE PROBLEM IN YOUR REPO ***
# ==========================================================================
# Your folders are named:
#     "Data structure "   (with a trailing space!)
#     "Async programming " (trailing space)
#     "type Hints"        (space)
#     "args-kwargs"       (hyphen)
#
# A module name must be a valid Python IDENTIFIER. None of those are.

candidates = ["Data structure ", "Async programming ", "type Hints", "args-kwargs"]
for name in candidates:
    print(f"8.1  {name!r:22} importable? {name.isidentifier()}")

# So you can RUN those files, but you can never `import` from them. That's
# fine for isolated practice scripts and fatal for an application, where
# every file imports every other.
#
# Rules for directory/module names:
#   lowercase, no spaces, underscores not hyphens, don't shadow stdlib.
#     data_structures/   async_programming/   type_hints/   args_kwargs/


# ==========================================================================
# 9. THE LAYOUT TO USE FOR YOUR FASTAPI PROJECT
# ==========================================================================
LAYOUT = """
    my-api/                      <- repo root (hyphens fine HERE, it's not a module)
    |-- pyproject.toml
    |-- .env                     <- secrets, gitignored
    |-- alembic/                 <- DB migrations
    |-- app/                     <- THE package (valid identifier)
    |   |-- __init__.py
    |   |-- main.py              <- FastAPI() instance + include_router
    |   |-- config.py            <- Settings (BaseSettings). Imports nothing.
    |   |-- database.py          <- engine, SessionLocal, get_db dependency
    |   |-- dependencies.py      <- shared Depends() functions
    |   |-- models/              <- SQLAlchemy tables (DB shape)
    |   |   |-- __init__.py
    |   |   `-- product.py
    |   |-- schemas/             <- Pydantic models (API shape)
    |   |   |-- __init__.py
    |   |   `-- product.py
    |   |-- routers/             <- APIRouter per resource
    |   |   |-- __init__.py
    |   |   `-- products.py
    |   `-- services/            <- business logic, no FastAPI imports
    |       |-- __init__.py
    |       `-- catalog.py
    `-- tests/
        |-- __init__.py
        `-- test_products.py
"""
print("9.1  recommended layout:", LAYOUT)

# The dependency direction, and why models/ and schemas/ are separate:
#
#     config  <- database <- models <- services <- routers <- main
#
# Each layer imports only from its left. Never the other way. Follow that and
# circular imports simply cannot happen.
#
# models/  = what the DATABASE stores   (SQLAlchemy)
# schemas/ = what the API accepts/returns (Pydantic)
# Keeping them apart is what stops you leaking password hashes in a response.


# ==========================================================================
# 10. RUNNING IT
# ==========================================================================
# Your repo already uses uv, so:
#
#     uv add "sqlalchemy>=2.0" alembic aiosqlite      # or asyncpg for postgres
#     uv add --dev pytest httpx
#     uv run uvicorn app.main:app --reload
#
# `app.main:app` = import the module app.main, take the attribute `app`.
# --reload watches your files and restarts. Never use it in production.
#
# And `python -m app.something` runs a module WITH package context, so
# relative imports keep working. `python app/something.py` does not.


# ==========================================================================
# EXERCISES
# ==========================================================================
print("\n" + "=" * 60 + "\nEXERCISES\n" + "=" * 60)

# --- E1 -------------------------------------------------------------------
# Add `shop/services/pricing.py` with `total_value() -> int` returning the sum
# of qty across all products. Import it from catalog.py WITHOUT creating a
# cycle. Then call it here.

# --- E2 -------------------------------------------------------------------
# Re-export get_product from shop/__init__.py so `from shop import get_product`
# works. Update __all__. Does this create a cycle? Why or why not?

# --- E3 -------------------------------------------------------------------
# Fix circular_a.py / circular_b.py using fix (b) from §7 — the deferred
# import. Then uncomment:
# import circular_a
# assert circular_a.a_func() == "a -> b"

# --- E4 -------------------------------------------------------------------
# Now fix the SAME pair using fix (a) instead: extract the shared piece into
# circular_shared.py so neither imports the other. Which fix is better here?

# --- E5 -------------------------------------------------------------------
# Create `shop/routers/orders.py` with `create(name, qty)` that uses
# get_product and raises ValueError when stock is insufficient.
# Use relative imports, matching products.py.

# --- E6 -------------------------------------------------------------------
# Rename your four broken folders to valid module names and add __init__.py
# to each, so this works:
#     from data_structures import drill_01_collections
# (Do it with `git mv` so history is preserved.)

# --- E7 -------------------------------------------------------------------
# Build the §9 skeleton for real, as empty files, under a new `my-api/`
# directory. Then write app/config.py with a Settings class and app/main.py
# that imports it. Confirm `uv run python -c "import app.main"` works.

print("Uncomment the asserts as you solve each one. Silence = all passed.")
