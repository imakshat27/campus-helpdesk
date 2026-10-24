"""Apply the frozen schema against an isolated test DB and compare to the ORM."""
import importlib.util
from pathlib import Path
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.autogenerate import compare_metadata
from sqlalchemy import create_engine
from app.models import Base

def test_initial_migration_matches_orm_and_downgrades(monkeypatch):
    path=Path(__file__).resolve().parents[1]/'alembic/versions/001_initial.py'
    spec=importlib.util.spec_from_file_location('initial_migration',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    engine=create_engine('sqlite://')
    with engine.begin() as conn:
        def compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
            # SQLite reflects VECTOR(384) as NUMERIC(384); verify its dimension
            # here rather than treating SQLite as a pgvector integration test.
            if metadata_column.name == 'embedding':
                assert inspected_type.precision == metadata_type.dim == 384
                return False
            return None
        ctx=MigrationContext.configure(conn,opts={'compare_type':compare_type})
        operations=Operations(ctx)
        class TestOps:
            def execute(self,sql):
                # SQLite cannot create Postgres extensions; everything else is real DDL.
                assert sql=='CREATE EXTENSION IF NOT EXISTS vector'
            def __getattr__(self,key):return getattr(operations,key)
        monkeypatch.setattr(module,'op',TestOps())
        module.upgrade()
        second_path=path.parent/'002_source_provenance.py'
        spec2=importlib.util.spec_from_file_location('source_migration',second_path)
        second=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(second)
        monkeypatch.setattr(second,'op',TestOps())
        second.upgrade()
        assert compare_metadata(ctx,Base.metadata)==[]
        second.downgrade()
        module.downgrade()
        from sqlalchemy import inspect
        assert inspect(conn).get_table_names()==[]
