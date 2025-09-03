import sys
import time
import traceback

import click
import sqlparse
from debug_toolbar.panels.sqlalchemy import SQLAlchemyPanel as BasePanel
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import SqlLexer
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.schema import DDL, MetaData

from nmdc_server.config import settings
from nmdc_server.multiomics import MultiomicsValue
from nmdc_server.utils import json_serializer


def pretty_format_sql(sql, params=None):
    """
    Interpolate SQL with params and add formatting and syntax highlighting.
    """
    if params and isinstance(params, dict):
        sql = sql % {k: repr(v) for k, v in params.items()}
    elif params:
        raise Exception("Failed to format SQL for debug logging")

    sql = sqlparse.format(
        sql,
        reindent=True,
        keyword_case="upper",
        wrap_after=80,
        strip_whitespace=True,
    )

    return highlight(sql, SqlLexer(), TerminalFormatter())


def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())


def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info["query_start_time"].pop()

    stack = traceback.extract_stack()

    caller = None
    for frame in reversed(stack[:-1]):  # skip the current frame
        # ignore frames that come from sqlalchemy directly
        if "sqlalchemy" not in frame.filename:
            caller = frame
            break

    if not executemany:
        parameters = [parameters]

    for parameter_set in parameters:
        formatted_sql = pretty_format_sql(statement, parameter_set)
        click.echo(formatted_sql, file=sys.stderr, nl=False)

        if caller:
            click.secho(
                f"Source: {caller.filename}:{caller.lineno}",
                fg="yellow",
                file=sys.stderr,
            )
        # This is technically the execution time for all of the queries in this commit. So for bulk
        # operations, this will be the total execution time for the entire operation.
        click.secho("Execution time: {:.3f}s\n".format(total), fg="red", bold=True, file=sys.stderr)


_engine_kwargs = {
    "json_serializer": json_serializer,
    "pool_size": settings.db_pool_size,
    "max_overflow": settings.db_pool_max_overflow,
    "future": True,
}
engine = create_engine(settings.current_db_uri, **_engine_kwargs)
engine_ingest = create_engine(settings.ingest_database_uri, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocalIngest = sessionmaker(autocommit=False, autoflush=False, bind=engine_ingest)


class SQLAlchemyPanel(BasePanel):
    async def add_engines(self, request):
        self.engines.add(engine)


# This is to avoid having to manually name all constraints
# See: http://alembic.zzzcomputing.com/en/latest/naming.html
metadata = MetaData(
    naming_convention={
        "pk": "pk_%(table_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
    },
)

Base = declarative_base(metadata=metadata)

update_nmdc_functions_sql = DDL(
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
                when op = 'like' then (lhs_ ILIKE rhs_)
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
            and tablename <> 'authorization_code'
            and tablename <> 'bulk_download'
            and tablename <> 'bulk_download_data_object'
            and tablename <> 'file_download'
            and tablename <> 'ingest_lock'
            and tablename <> 'invalidated_token';
BEGIN
    FOR stmt IN statements LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(stmt.tablename) || ' CASCADE;';
    END LOOP;
END;
$$ LANGUAGE plpgsql;
    """
)

# define functions used for comparison between arbitrary types
listen(
    metadata,
    "before_create",
    update_nmdc_functions_sql,
)

# A SQL function used to populate denormalized multiomics bitmasks
update_multiomics_sql = DDL(
    f"""
with m as (select
    b.id as id,
    bit_or(
        case
            when op.annotations->>'omics_type' = 'Metabolomics' then
                b'{MultiomicsValue.mb.value:07b}'
            when op.annotations->>'omics_type' = 'Metagenome' then
                b'{MultiomicsValue.mg.value:07b}'
            when op.annotations->>'omics_type' = 'Proteomics' then
                b'{MultiomicsValue.mp.value:07b}'
            when op.annotations->>'omics_type' = 'Metatranscriptome' then
                b'{MultiomicsValue.mt.value:07b}'
            when op.annotations->>'omics_type' = 'Organic Matter Characterization' then
                b'{MultiomicsValue.om.value:07b}'
            when op.annotations->>'omics_type' = 'Lipidomics' then
                b'{MultiomicsValue.li.value:07b}'
            when op.annotations->>'omics_type' = 'Amplicon' then
                b'{MultiomicsValue.am.value:07b}'

        end
    )::integer as multiomics
from biosample b
    join biosample_input_association bia on bia.biosample_id = b.id
    join omics_processing op on bia.omics_processing_id = op.id
group by b.id)
update biosample set multiomics = m.multiomics
from m
where m.id = biosample.id;

with m as (select
    s.id as id,
    bit_or(
        case
            when op.annotations->>'omics_type' = 'Metabolomics' then
                b'{MultiomicsValue.mb.value:07b}'
            when op.annotations->>'omics_type' = 'Metagenome' then
                b'{MultiomicsValue.mg.value:07b}'
            when op.annotations->>'omics_type' = 'Proteomics' then
                b'{MultiomicsValue.mp.value:07b}'
            when op.annotations->>'omics_type' = 'Metatranscriptome' then
                b'{MultiomicsValue.mt.value:07b}'
            when op.annotations->>'omics_type' = 'Organic Matter Characterization' then
                b'{MultiomicsValue.om.value:07b}'
            when op.annotations->>'omics_type' = 'Lipidomics' then
                b'{MultiomicsValue.li.value:07b}'
            when op.annotations->>'omics_type' = 'Amplicon' then
                b'{MultiomicsValue.am.value:07b}'
        end
    )::integer as multiomics
from study s
    join biosample b on s.id = b.study_id
    join biosample_input_association bia on b.id = bia.biosample_id
    join omics_processing op on bia.omics_processing_id = op.id
group by s.id)
update study set multiomics = m.multiomics
from m
where m.id = study.id;
"""
)


def get_db():
    with SessionLocal() as db:
        yield db
