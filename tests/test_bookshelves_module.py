from fastapi import APIRouter


def test_bookshelves_module_import_and_router_exists():
    from app.routes import bookshelves

    assert bookshelves.router is not None
    assert isinstance(bookshelves.router, APIRouter)


def test_bookshelves_router_has_no_active_routes_yet():
    from app.routes import bookshelves

    # The route handlers in this module are currently commented out.
    assert bookshelves.router.routes == []
