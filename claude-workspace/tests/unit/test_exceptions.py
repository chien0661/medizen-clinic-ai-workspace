"""Unit tests: AppException subclasses and exception handler response shapes."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import (
    AppException,
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    OptimisticLockError,
    register_exception_handlers,
)

# ---------------------------------------------------------------------------
# AppException subclass attributes
# ---------------------------------------------------------------------------


def test_not_found_error_defaults():
    exc = NotFoundError()
    assert exc.code == "NOT_FOUND"
    assert exc.http_status == 404
    assert exc.message == "Resource not found"


def test_not_found_error_custom_message():
    exc = NotFoundError(message="Patient not found", details={"id": "abc"})
    assert exc.message == "Patient not found"
    assert exc.details == {"id": "abc"}


def test_conflict_error_defaults():
    exc = ConflictError()
    assert exc.code == "CONFLICT"
    assert exc.http_status == 409


def test_forbidden_error_defaults():
    exc = ForbiddenError()
    assert exc.code == "FORBIDDEN"
    assert exc.http_status == 403


def test_business_rule_error_defaults():
    exc = BusinessRuleError()
    assert exc.code == "BUSINESS_RULE_VIOLATION"
    assert exc.http_status == 400


def test_optimistic_lock_error_defaults():
    exc = OptimisticLockError()
    assert exc.code == "OPTIMISTIC_LOCK_CONFLICT"
    assert exc.http_status == 409


def test_app_exception_is_base():
    """All concrete exceptions are AppException subclasses."""
    for cls in (NotFoundError, ConflictError, ForbiddenError, BusinessRuleError, OptimisticLockError):
        assert issubclass(cls, AppException)


def test_app_exception_empty_details_default():
    """details defaults to empty dict, not None."""
    exc = NotFoundError()
    assert exc.details == {}


# ---------------------------------------------------------------------------
# Handler response shape (JSON contract)
# ---------------------------------------------------------------------------


def _build_test_app() -> FastAPI:
    """Build a minimal app with exception handlers and test routes."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/raise-not-found")
    async def raise_not_found():
        raise NotFoundError(message="thing missing", details={"resource": "thing"})

    @test_app.get("/raise-app-exc")
    async def raise_app_exc():
        raise ConflictError(message="already exists")

    @test_app.get("/raise-unhandled")
    async def raise_unhandled():
        raise RuntimeError("something broke internally")

    return test_app


@pytest.fixture
async def test_client():
    """Test client with raise_app_exceptions=False so our custom 500 handler is exercised."""
    app = _build_test_app()
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as ac:
        yield ac


async def test_not_found_handler_status(test_client):
    resp = await test_client.get("/raise-not-found")
    assert resp.status_code == 404


async def test_not_found_handler_error_shape(test_client):
    resp = await test_client.get("/raise-not-found")
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"] == "thing missing"
    assert body["error"]["details"] == {"resource": "thing"}


async def test_not_found_handler_meta_shape(test_client):
    """Response must include meta.request_id."""
    resp = await test_client.get("/raise-not-found")
    body = resp.json()
    assert "meta" in body
    assert "request_id" in body["meta"]


async def test_conflict_handler_status(test_client):
    resp = await test_client.get("/raise-app-exc")
    assert resp.status_code == 409


async def test_unhandled_exception_handler_returns_500(test_client):
    resp = await test_client.get("/raise-unhandled")
    assert resp.status_code == 500


async def test_unhandled_exception_handler_error_shape(test_client):
    resp = await test_client.get("/raise-unhandled")
    body = resp.json()
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "request_id" in body["meta"]
