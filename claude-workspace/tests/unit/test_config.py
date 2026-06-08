"""Unit tests: verify Settings load correctly from environment."""

from app.core.config import Settings


def test_settings_defaults():
    """Settings should have sane defaults when required fields are provided."""
    s = Settings(
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
        REDIS_URL="redis://localhost:6379/0",
        JWT_SECRET="test-secret-at-least-8-chars",
    )
    assert s.JWT_ALGORITHM == "HS256"
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert s.REFRESH_TOKEN_EXPIRE_DAYS == 7
    assert s.LOCKOUT_MAX_ATTEMPTS == 5
    # ENVIRONMENT and DEBUG may be overridden by container env; assert types only
    assert isinstance(s.ENVIRONMENT, str)
    assert isinstance(s.DEBUG, bool)


def test_settings_loads_from_env(monkeypatch):
    """Settings should read values from environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://env:env@db:5432/envdb")
    monkeypatch.setenv("REDIS_URL", "redis://envredis:6379/1")
    monkeypatch.setenv("JWT_SECRET", "env-secret-12chars")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

    s = Settings()

    assert s.DATABASE_URL == "postgresql+asyncpg://env:env@db:5432/envdb"
    assert s.REDIS_URL == "redis://envredis:6379/1"
    assert s.JWT_SECRET == "env-secret-12chars"
    assert s.ENVIRONMENT == "production"
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 30


def test_settings_cors_origins_json_parse(monkeypatch):
    """CORS_ORIGINS should parse correctly from a JSON string in env."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("JWT_SECRET", "test-secret-12chars")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        '["https://app.example.com", "https://admin.example.com"]',
    )

    s = Settings()

    assert isinstance(s.CORS_ORIGINS, list)
    assert "https://app.example.com" in s.CORS_ORIGINS
    assert "https://admin.example.com" in s.CORS_ORIGINS
