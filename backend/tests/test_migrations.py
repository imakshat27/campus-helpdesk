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
        third_path=path.parent/'003_access_control.py'
        spec3=importlib.util.spec_from_file_location('access_migration',third_path)
        third=importlib.util.module_from_spec(spec3);spec3.loader.exec_module(third)
        monkeypatch.setattr(third,'op',TestOps())
        third.upgrade()
        # Freeze realistic legacy data before applying account/chat migrations.
        import sqlalchemy as sa
        connection=conn
        connection.execute(sa.text("INSERT INTO conversations (id,created_at,owner) VALUES ('legacy','2026-10-01 00:00:00','anonymous-owner')"))
        for mid in ['b','a','c']:
            connection.execute(sa.text("INSERT INTO messages (id,conversation_id,role,content,sources,created_at) VALUES (:id,'legacy','user','legacy question','[]','2026-10-01 00:00:00')"),{'id':mid})
        for tid in ['older','newer']:
            connection.execute(sa.text("INSERT INTO tickets (id,reference,conversation_id,query,reason,status,created_at) VALUES (:id,:reference,'legacy','legacy question','Confirmed','open',:created)"),{'id':tid,'reference':'HD-'+tid,'created':'2026-10-02 00:00:00' if tid=='newer' else '2026-10-01 00:00:00'})
        spec4=importlib.util.spec_from_file_location('account_migration',path.parent/'004_account_sessions.py')
        fourth=importlib.util.module_from_spec(spec4);spec4.loader.exec_module(fourth)
        monkeypatch.setattr(fourth,'op',TestOps())
        fourth.upgrade()
        spec5=importlib.util.spec_from_file_location('chat_migration',path.parent/'005_persistent_chat.py')
        fifth=importlib.util.module_from_spec(spec5);spec5.loader.exec_module(fifth)
        monkeypatch.setattr(fifth,'op',TestOps())
        fifth.upgrade()
        assert connection.execute(sa.text("SELECT id,sequence FROM messages ORDER BY sequence")).all()==[('a',1),('b',2),('c',3)]
        assert connection.execute(sa.text("SELECT owner,state,next_sequence FROM conversations WHERE id='legacy'")).one()==('anonymous-owner','waiting_for_staff',4)
        assert connection.execute(sa.text("SELECT id,status FROM tickets ORDER BY id")).all()==[('newer','open'),('older','resolved')]
        spec6=importlib.util.spec_from_file_location('events_migration',path.parent/'006_websocket_tickets.py')
        sixth=importlib.util.module_from_spec(spec6);spec6.loader.exec_module(sixth)
        monkeypatch.setattr(sixth,'op',TestOps())
        sixth.upgrade()
        assert compare_metadata(ctx,Base.metadata)==[]
        sixth.downgrade()
        fifth.downgrade()
        fourth.downgrade()
        third.downgrade()
        second.downgrade()
        module.downgrade()
        from sqlalchemy import inspect
        assert inspect(conn).get_table_names()==[]
