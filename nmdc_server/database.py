from contextlib import contextmanager
from datetime import datetime
import json
from typing import Any, Iterator, Optional

from sqlalchemy import create_engine as _create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import DDL, MetaData

from nmdc_server.config import settings


_engine: Optional[Engine] = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

# This is to avoid having to manually name all constraints
# See: http://alembic.zzzcomputing.com/en/latest/naming.html
metadata = MetaData(
    naming_convention={
        "pk": "pk_%(table_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
    }
)

Base = declarative_base(metadata=metadata)


listen(
    metadata,
    "before_create",
    DDL(
        """
create or replace function nmdc_compare (lhs text, op text, rhs text)
returns boolean as $$
    declare
        result boolean;
        lhs_ alias for lhs;
        rhs_ alias for rhs;
    begin
        select
            case
                when op = '==' then (lhs_ = rhs_)
                when op = '<' then (lhs_ < rhs_)
                when op = '<=' then (lhs_ <= rhs_)
                when op = '>' then (lhs_ > rhs_)
                when op = '>=' then (lhs_ >= rhs_)
                when op = '!=' then (lhs_ <> rhs_)
            end into result;
        return result;
    end;
$$
language plpgsql
immutable;

create or replace function nmdc_compare (lhs text, op text, rhs numeric)
returns boolean as $$
    declare
        result boolean;
        lhs_ numeric;
        rhs_ alias for rhs;
    begin
        lhs_ := cast(lhs as numeric);
        select
            case
                when op = '==' then (lhs_ = rhs_)
                when op = '<' then (lhs_ < rhs_)
                when op = '<=' then (lhs_ <= rhs_)
                when op = '>' then (lhs_ > rhs_)
                when op = '>=' then (lhs_ >= rhs_)
                when op = '!=' then (lhs_ <> rhs_)
            end into result;
        return result;
    end;
$$
language plpgsql
immutable;

create or replace function nmdc_compare (lhs text, op text, rhs timestamp)
returns boolean as $$
    declare
        result boolean;
        lhs_ timestamp;
        rhs_ alias for rhs;
    begin
        lhs_ := cast(lhs as timestamp);
        select
            case
                when op = '==' then (lhs_ = rhs_)
                when op = '<' then (lhs_ < rhs_)
                when op = '<=' then (lhs_ <= rhs_)
                when op = '>' then (lhs_ > rhs_)
                when op = '>=' then (lhs_ >= rhs_)
                when op = '!=' then (lhs_ <> rhs_)
            end into result;
        return result;
    end;
$$
language plpgsql;

CREATE OR REPLACE FUNCTION truncate_tables() RETURNS void AS $$
DECLARE
    statements CURSOR FOR
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
            and tablename <> 'alembic_version'
            and tablename <> 'file_download'
            and tablename <> 'ingest_lock';
BEGIN
    FOR stmt IN statements LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(stmt.tablename) || ' CASCADE;';
    END LOOP;
END;
$$ LANGUAGE plpgsql;
"""
    ),
)

#: This variable configures whether or not we are connecting to the testing
#  database or not.  This isn't really ideal, but I can't find a way to shim
#  the configuration into fastapi dependencies more cleanly in a way that also
#  supports factory-boy's scoped sessions.
testing = False


def json_serializer(data: Any) -> str:
    def default_(val: Any) -> str:
        if isinstance(val, datetime):
            return val.isoformat()
        raise TypeError(f"Cannot serialize {val}")

    return json.dumps(data, default=default_)


def create_engine() -> Engine:
    global _engine

    if testing or _engine is None:
        uri = settings.database_uri
        if testing:
            uri = settings.testing_database_uri

        _engine = _create_engine(uri, json_serializer=json_serializer)

    return _engine


@contextmanager
def create_session() -> Iterator[Session]:
    engine = create_engine()
    SessionLocal.configure(bind=engine)
    metadata.bind = engine

    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
