-- TODO: Document what this role is (why we create it).
create role nmdc_data_reader;

-- Note: "nmdc_reader" is a role the administrators of the `nmdc_a` and `nmdc_b` databases use to
-- give people (i.e. NMDC team members) read-only access to those databases.
-- Reference: https://github.com/microbiomedata/infra-admin/blob/main/postgres/user-management.md
create role nmdc_reader;

create database nmdc_a;
create database nmdc_b;
