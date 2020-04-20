from contextlib import contextmanager
from datetime import datetime
import json
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import DDL

from nmdc_server.config import Settings


SessionLocal = sessionmaker(autocommit=False, autoflush=False)

Base = declarative_base()

listen(
    Base.metadata,
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
"""
    ),
)


def json_serializer(data: Any) -> str:
    def default_(val: Any) -> str:
        if isinstance(val, datetime):
            return val.isoformat()
        raise TypeError(f'Cannot serialize {val}')
    return json.dumps(data, default=default_)


@contextmanager
def create_session(settings: Settings):
    engine = create_engine(settings.database_uri, json_serializer=json_serializer)
    session.configure(bind=engine)
    Base.metadata.bind = engine

    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
