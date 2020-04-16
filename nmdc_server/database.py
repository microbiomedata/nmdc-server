from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import DDL

from nmdc_server.config import settings


SQLALCHEMY_DATABASE_URL = settings.database_uri

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
