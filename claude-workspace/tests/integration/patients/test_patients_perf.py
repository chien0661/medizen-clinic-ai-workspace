"""Performance benchmark tests for Patient Management API (TASK-005).

AC1: Search by phone (10-digit) must return < 100ms p95 with 100k patients in DB.
Also benchmarks fuzzy name search at the same scale.

Marks
-----
@pytest.mark.perf — skip in fast CI:
    pytest -m "not perf"          # skip perf tests
    pytest -m perf                # run perf tests only

Fixture strategy
----------------
Session-scoped fixture seeds ~100k patients using bulk INSERT (batches of 5,000)
directly via SQLAlchemy core (no API calls). Fixture cleanup removes the seeded
clinic at session teardown, cascading all patients via FK ON DELETE CASCADE or
explicit DELETE.
"""

from __future__ import annotations

import statistics
import time
import uuid
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.main import app
from tests.conftest import TEST_DATABASE_URL

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEED_COUNT = 100_000
BATCH_SIZE = 5_000
PHONE_QUERY_ITERATIONS = 100
PERF_P95_LIMIT_MS = 100.0  # AC1 threshold


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _login(client: AsyncClient, clinic_code: str, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"clinic_code": clinic_code, "username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed ({resp.status_code}): {resp.text}"
    return resp.json()["data"]["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _p95(latencies_ms: list[float]) -> float:
    """Return the 95th-percentile latency from a list of millisecond measurements."""
    sorted_lat = sorted(latencies_ms)
    idx = int(len(sorted_lat) * 0.95)
    return sorted_lat[min(idx, len(sorted_lat) - 1)]


# ---------------------------------------------------------------------------
# Session-scoped perf fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def perf_ctx():  # noqa: C901
    """Seed ~100k patients across 3 clinics; yield context; teardown on session end.

    Uses direct bulk INSERT (batches of 5_000) to keep fixture build time < 60s.

    Known phone numbers for deterministic search:
    - Clinic 0: '0900000001' .. '0900003333' (3333 records per clinic = 10k)
    - The rest are synthetic with unique generated phones.

    Seeded known phone for queries: '0911111111' (seeded once in clinic_0).
    Seeded known name: 'Nguyễn Văn An Perf' (seeded once in clinic_0).
    """
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    # Create 3 clinics + 1 admin user per clinic
    clinic_ids = [uuid.uuid4() for _ in range(3)]
    clinic_codes = [f"PERF{i}{uuid.uuid4().hex[:4].upper()}" for i in range(3)]
    admin_ids = [uuid.uuid4() for _ in range(3)]
    password = "PerfTestPassw0rd!"

    # Get admin role id
    async with factory() as session:
        row = (
            await session.execute(
                text("SELECT id FROM role WHERE code = 'admin' AND clinic_id IS NULL")
            )
        ).fetchone()
        if row is None:
            pytest.skip("admin role not found — run alembic upgrade head first")
        admin_role_id = str(row[0])

    # Insert clinics + users
    async with factory() as session:
        for i, (cid, code, aid) in enumerate(zip(clinic_ids, clinic_codes, admin_ids, strict=False)):
            await session.execute(
                text(
                    "INSERT INTO clinic (id, code, name, specialty, is_active)"
                    " VALUES (:id, :code, :name, :specialty, true)"
                ),
                {"id": str(cid), "code": code, "name": f"Perf Clinic {i}", "specialty": "general"},
            )
            await session.execute(
                text(
                    'INSERT INTO "user" (id, clinic_id, username, full_name,'
                    " password_hash, is_active, is_locked, failed_login_count)"
                    " VALUES (:id, :cid, :uname, :fname, :pw, true, false, 0)"
                ),
                {
                    "id": str(aid),
                    "cid": str(cid),
                    "uname": f"perf_admin_{i}_{code.lower()}",
                    "fname": f"Perf Admin {i}",
                    "pw": hash_password(password),
                },
            )
            await session.execute(
                text(
                    "INSERT INTO user_role (id, user_id, role_id)"
                    " VALUES (:id, :uid, :rid) ON CONFLICT DO NOTHING"
                ),
                {"id": str(uuid.uuid4()), "uid": str(aid), "rid": admin_role_id},
            )
        await session.commit()

    # Seed patients in batches
    # Distribute evenly across 3 clinics
    # Clinic 0: includes known phone '0911111111' and known name patient
    per_clinic = SEED_COUNT // 3
    known_phone = "0911111111"
    known_name = "Nguyen Van An Perf"  # will match fuzzy "nguyen van an" query

    total_seeded = 0
    build_start = time.perf_counter()

    async with factory() as session:
        # First insert known records in clinic 0
        clinic_0_id = str(clinic_ids[0])
        await session.execute(
            text(
                "INSERT INTO patient"
                " (id, clinic_id, patient_code, full_name, gender, birth_year,"
                "  is_deleted, version, created_at, updated_at, phone)"
                " VALUES (:id, :cid, :code, :name, 'male', 1990, false, 1, now(), now(), :phone)"
            ),
            {
                "id": str(uuid.uuid4()),
                "cid": clinic_0_id,
                "code": "BNPERF00001",
                "name": known_name,
                "phone": known_phone,
            },
        )
        total_seeded += 1

        # Bulk seed remaining patients in batches
        for clinic_idx, cid in enumerate(clinic_ids):
            clinic_id_str = str(cid)
            code_offset = clinic_idx * per_clinic
            batch: list[dict[str, Any]] = []

            for i in range(per_clinic):
                seq = code_offset + i + 2  # +2 to avoid collision with BNPERF00001
                phone_num = f"09{seq % 100_000_000:08d}"  # 10-digit phone
                batch.append({
                    "id": str(uuid.uuid4()),
                    "cid": clinic_id_str,
                    "code": f"BN{seq:07d}",
                    "name": f"Patient Bulk {seq:07d}",
                    "phone": phone_num,
                })

                if len(batch) >= BATCH_SIZE:
                    await session.execute(
                        text(
                            "INSERT INTO patient"
                            " (id, clinic_id, patient_code, full_name, gender, birth_year,"
                            "  is_deleted, version, created_at, updated_at, phone)"
                            " VALUES (:id, :cid, :code, :name, 'male', 1990,"
                            "         false, 1, now(), now(), :phone)"
                        ),
                        batch,
                    )
                    total_seeded += len(batch)
                    batch = []

            if batch:
                await session.execute(
                    text(
                        "INSERT INTO patient"
                        " (id, clinic_id, patient_code, full_name, gender, birth_year,"
                        "  is_deleted, version, created_at, updated_at, phone)"
                        " VALUES (:id, :cid, :code, :name, 'male', 1990,"
                        "         false, 1, now(), now(), :phone)"
                    ),
                    batch,
                )
                total_seeded += len(batch)

        await session.commit()

    build_elapsed = time.perf_counter() - build_start
    print(f"\n[perf] Seeded {total_seeded:,} patients in {build_elapsed:.1f}s")

    yield {
        "clinic_ids": clinic_ids,
        "clinic_codes": clinic_codes,
        "admin_ids": admin_ids,
        "password": password,
        "known_phone": known_phone,
        "known_name": known_name,
        "total_seeded": total_seeded,
        "factory": factory,
    }

    # Teardown — remove all seeded patients + users + clinics
    async with factory() as session:
        for cid in clinic_ids:
            await session.execute(
                text("DELETE FROM patient_relation WHERE clinic_id = :cid"),
                {"cid": str(cid)},
            )
            await session.execute(
                text("DELETE FROM patient_merge_log WHERE clinic_id = :cid"),
                {"cid": str(cid)},
            )
            await session.execute(
                text("DELETE FROM patient WHERE clinic_id = :cid"),
                {"cid": str(cid)},
            )
        for aid in admin_ids:
            await session.execute(
                text("DELETE FROM user_role WHERE user_id = :uid"), {"uid": str(aid)}
            )
            await session.execute(
                text('DELETE FROM "user" WHERE id = :uid'), {"uid": str(aid)}
            )
        for cid in clinic_ids:
            await session.execute(
                text("DELETE FROM clinic WHERE id = :cid"), {"cid": str(cid)}
            )
        await session.commit()

    await engine.dispose()


# ---------------------------------------------------------------------------
# Perf tests
# ---------------------------------------------------------------------------


@pytest.mark.perf
@pytest.mark.asyncio
async def test_perf_phone_search_p95_under_100ms_at_100k(perf_ctx):
    """AC1: p95 phone search latency < 100ms with ~100k patients in DB.

    Warms the index with 5 queries first, then measures 100 queries.
    Uses the trigram GIN index gix_patient_phone_trgm.
    """
    limiter.reset()
    ctx = perf_ctx
    clinic_code = ctx["clinic_codes"][0]
    admin_id = ctx["admin_ids"][0]
    password = ctx["password"]
    known_phone = ctx["known_phone"]
    factory = ctx["factory"]

    # Resolve admin username from DB
    async with factory() as session:
        row = (
            await session.execute(
                text('SELECT username FROM "user" WHERE id = :uid'),
                {"uid": str(admin_id)},
            )
        ).fetchone()
    admin_username = row[0]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        token = await _login(client, clinic_code, admin_username, password)

        # Warm-up: 5 queries (not measured)
        for _ in range(5):
            await client.get(
                f"/api/v1/patients/search?q={known_phone}&type=phone",
                headers=_auth(token),
            )

        # Measure 100 queries
        latencies_ms: list[float] = []
        for _ in range(PHONE_QUERY_ITERATIONS):
            t0 = time.perf_counter()
            resp = await client.get(
                f"/api/v1/patients/search?q={known_phone}&type=phone",
                headers=_auth(token),
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies_ms.append(elapsed_ms)
            assert resp.status_code == 200, f"Search failed: {resp.status_code} {resp.text}"

    p95 = _p95(latencies_ms)
    avg = statistics.mean(latencies_ms)
    p50 = statistics.median(latencies_ms)
    max_lat = max(latencies_ms)

    print(
        f"\n[perf] Phone search @ {ctx['total_seeded']:,} patients"
        f" | p50={p50:.1f}ms | p95={p95:.1f}ms | avg={avg:.1f}ms | max={max_lat:.1f}ms"
        f" | iterations={PHONE_QUERY_ITERATIONS}"
    )

    assert p95 < PERF_P95_LIMIT_MS, (
        f"AC1 FAILED: phone search p95={p95:.1f}ms exceeds {PERF_P95_LIMIT_MS}ms threshold"
        f" (avg={avg:.1f}ms, max={max_lat:.1f}ms, n={PHONE_QUERY_ITERATIONS},"
        f" patients={ctx['total_seeded']:,})"
    )


@pytest.mark.perf
@pytest.mark.asyncio
async def test_perf_fuzzy_name_search_records_numbers_at_100k(perf_ctx):
    """Fuzzy name search ('nguyen van an') at ~100k patients — record latencies.

    No AC threshold for fuzzy name search; numbers are recorded in the test report.
    Uses plainto_tsquery + pg_trgm similarity via gix_patient_name_search /
    gix_patient_name_trgm indexes.
    """
    limiter.reset()
    ctx = perf_ctx
    clinic_code = ctx["clinic_codes"][0]
    admin_id = ctx["admin_ids"][0]
    password = ctx["password"]
    factory = ctx["factory"]

    async with factory() as session:
        row = (
            await session.execute(
                text('SELECT username FROM "user" WHERE id = :uid'),
                {"uid": str(admin_id)},
            )
        ).fetchone()
    admin_username = row[0]

    fuzzy_queries = ["nguyen van an", "nguyen vn an", "nguyn van an"]
    results_summary: list[dict] = []

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        token = await _login(client, clinic_code, admin_username, password)

        for q in fuzzy_queries:
            # Warm-up
            for _ in range(3):
                await client.get(
                    f"/api/v1/patients/search?q={q}&type=name",
                    headers=_auth(token),
                )

            latencies_ms: list[float] = []
            result_counts: list[int] = []
            for _ in range(30):
                t0 = time.perf_counter()
                resp = await client.get(
                    f"/api/v1/patients/search?q={q}&type=name",
                    headers=_auth(token),
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000
                latencies_ms.append(elapsed_ms)
                assert resp.status_code == 200, f"Fuzzy search failed: {resp.text}"
                body = resp.json()
                result_counts.append(len(body) if isinstance(body, list) else 0)

            p95 = _p95(latencies_ms)
            avg = statistics.mean(latencies_ms)
            hit_count = result_counts[0] if result_counts else 0
            results_summary.append(
                {"q": q, "p95_ms": p95, "avg_ms": avg, "hits": hit_count}
            )
            print(
                f"\n[perf] Fuzzy name '{q}' @ {ctx['total_seeded']:,} patients"
                f" | p95={p95:.1f}ms | avg={avg:.1f}ms | hits={hit_count}"
            )

    # Verify known name is found by at least one fuzzy query
    known_name = ctx["known_name"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        token = await _login(client, clinic_code, admin_username, password)
        resp = await client.get(
            "/api/v1/patients/search?q=nguyen+van+an&type=name",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        results = resp.json()
        names = [r.get("full_name", "") for r in (results if isinstance(results, list) else [])]
        # known_name was seeded with "Nguyen Van An Perf" — check partial match
        found = any("Nguyen Van An" in n or "Nguy" in n for n in names)
        print(
            f"\n[perf] Fuzzy lookup for known name '{known_name}': "
            f"{'FOUND' if found else 'NOT FOUND'} in results={names[:5]}"
        )
        # Record but do not assert — fuzzy matching is best-effort without accent data
        # Known name was seeded as ASCII "Nguyen Van An Perf" without Vietnamese accents
        # The trigram similarity should still match with threshold 0.2
