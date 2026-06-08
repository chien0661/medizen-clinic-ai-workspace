"""Unit tests: verify mixin columns are present on BaseEntity."""

import sqlalchemy as sa

from app.core.base_model import Base, BaseEntity


class _ConcreteEntity(BaseEntity):
    """Minimal concrete entity to test BaseEntity columns."""

    __tablename__ = "_test_concrete_entity"
    __table_args__ = {"extend_existing": True}


def _col_names(model) -> set[str]:
    return {c.key for c in sa.inspect(model).mapper.column_attrs}


def test_timestamp_mixin_columns():
    cols = _col_names(_ConcreteEntity)
    assert "created_at" in cols
    assert "updated_at" in cols


def test_soft_delete_mixin_columns():
    cols = _col_names(_ConcreteEntity)
    assert "is_deleted" in cols
    assert "deleted_at" in cols
    assert "deleted_by" in cols


def test_tenant_mixin_columns():
    cols = _col_names(_ConcreteEntity)
    assert "clinic_id" in cols


def test_audited_mixin_columns():
    cols = _col_names(_ConcreteEntity)
    assert "created_by" in cols
    assert "updated_by" in cols


def test_versioned_mixin_columns():
    cols = _col_names(_ConcreteEntity)
    assert "version" in cols


def test_base_entity_has_uuid_pk():
    cols = _col_names(_ConcreteEntity)
    assert "id" in cols
    pk_cols = [c for c in _ConcreteEntity.__table__.primary_key.columns]
    assert len(pk_cols) == 1
    assert pk_cols[0].name == "id"


def test_base_entity_is_abstract():
    assert BaseEntity.__abstract__ is True


def test_base_is_declarative():
    assert issubclass(Base, sa.orm.DeclarativeBase)
