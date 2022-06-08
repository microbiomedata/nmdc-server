from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import DDL, MetaData

from nmdc_server.config import settings
from nmdc_server.multiomics import MultiomicsValue
from nmdc_server.utils import json_serializer

_engine_kwargs = {
    "json_serializer": json_serializer,
    "echo": settings.print_sql,
    "pool_size": settings.db_pool_size,
    "max_overflow": settings.db_pool_max_overflow,
}
engine = create_engine(settings.current_db_uri, **_engine_kwargs)
engine_ingest = create_engine(settings.ingest_database_uri, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocalIngest = sessionmaker(autocommit=False, autoflush=False, bind=engine_ingest)

# This is to avoid having to manually name all constraints
# See: http://alembic.zzzcomputing.com/en/latest/naming.html
metadata = MetaData(
    bind=engine,
    naming_convention={
        "pk": "pk_%(table_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
    },
)

Base = declarative_base(metadata=metadata)

# define functions used for comparison between arbitrary types
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

/*
A convenience function to truncate all tables that get repopulated
during an ingest.  Any tables storing persistent data should be
added as an exception here.
*/
CREATE OR REPLACE FUNCTION truncate_tables() RETURNS void AS $$
DECLARE
    statements CURSOR FOR
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
            and tablename <> 'alembic_version'
            and tablename <> 'file_download'
            and tablename <> 'ingest_lock'
            and tablename <> 'bulk_download'
            and tablename <> 'bulk_download_data_object';
BEGIN
    FOR stmt IN statements LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(stmt.tablename) || ' CASCADE;';
    END LOOP;
END;
$$ LANGUAGE plpgsql;
"""
    ),
)

# A SQL function used to populate denormalized multiomics bitmasks
update_multiomics_sql = DDL(
    f"""
with m as (select
    b.id as id,
    bit_or(
        case
            when op.annotations->>'omics_type' = 'Metabolomics' then
                b'{MultiomicsValue.mb.value:05b}'
            when op.annotations->>'omics_type' = 'Metagenome' then
                b'{MultiomicsValue.mg.value:05b}'
            when op.annotations->>'omics_type' = 'Proteomics' then
                b'{MultiomicsValue.mp.value:05b}'
            when op.annotations->>'omics_type' = 'Metatranscriptome' then
                b'{MultiomicsValue.mt.value:05b}'
            when op.annotations->>'omics_type' = 'Organic Matter Characterization' then
                b'{MultiomicsValue.om.value:05b}'
        end
    )::integer as multiomics
from biosample b join omics_processing op on op.biosample_id = b.id
group by b.id)
update biosample set multiomics = m.multiomics
from m
where m.id = biosample.id;

with m as (select
    s.id as id,
    bit_or(
        case
            when op.annotations->>'omics_type' = 'Metabolomics' then
                b'{MultiomicsValue.mb.value:05b}'
            when op.annotations->>'omics_type' = 'Metagenome' then
                b'{MultiomicsValue.mg.value:05b}'
            when op.annotations->>'omics_type' = 'Proteomics' then
                b'{MultiomicsValue.mp.value:05b}'
            when op.annotations->>'omics_type' = 'Metatranscriptome' then
                b'{MultiomicsValue.mt.value:05b}'
            when op.annotations->>'omics_type' = 'Organic Matter Characterization' then
                b'{MultiomicsValue.om.value:05b}'
        end
    )::integer as multiomics
from study s
    join biosample b on s.id = b.study_id
    join omics_processing op on op.biosample_id = b.id
group by s.id)
update study set multiomics = m.multiomics
from m
where m.id = study.id;
"""
)


def get_db():
    with SessionLocal() as db:
        yield db
