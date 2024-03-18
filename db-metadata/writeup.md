---
title: Speed-Dating your Database with Postgres Information Schema
published: false
description: 
tags: 
# cover_image: https://direct_url_to_image.jpg
# Use a ratio of 100:42 for best results.
# published_at: 2024-01-24 01:25 +0000
---
[TODO] Table of Contents
[TODO] List of Sources

## Intro

If you've worked with SQL before, you're familiar with writing queries to ask questions about the _data_ in your database. Give me all the people that user A follows. Tell me how many sales we made in the last week. 

Databases are good for asking questions about your data, but they also store _metadata_ about the data in your database. PostgreSQL in particular stores data about Table names, schemas, indexes, views and much more. And it's just a few sql queries away from you.


## Querying Metadata in PostgreSQL
PostgreSQL stores metadata for the database in 3 areas: The Information Schema, System Views, and System Catalogs.


### [The Information Schema](https://www.postgresql.org/docs/16/information-schema.html)

Postgres' Information Schema "consists of a set of views that contain information about the objects defined in the current database." A database schema is essentially a way to put tables into their own group. By default, any tables you create in Postgres are part of a database schema called "public". 

Though you'll typically query your tables like:
```sql
SELECT * FROM my_table LIMIT 10;
```

You can also include the schema as part of your query like so:

```sql
SELECT * FROM public.my_table LIMIT 10;
```

The _information schema_, as its name suggests, is a schema in your Postgres Database with tables that store data _about_ the data in your database. You can write queries against the tables in this schema to learn more about your database(s).

You can find the full list of tables in the information schema [in the Postgres Docs](https://www.postgresql.org/docs/16/information-schema.html), but I'm sharing a few that are handy.


```sql
-- Find all the schemas in your database
select 
distinct table_schema 
from information_schema.tables; 
```

```sql
-- Find all the tables in your schema
select table_name 
from information_schema.tables 
where table_schema = 'public';
```

```sql
-- Information about the columns in a table
select 
  column_name,
  data_type, 
  column_default,
  is_nullable 
from information_schema.columns where table_name = 'sales';
```

```sql
-- Name of all the constraints for a given table
select * from information_schema.constraint_column_usage 
where table_schema ='public' 
and table_name ='sales';
```
### [System Views](https://www.postgresql.org/docs/current/views.html)

Postgres System Views are a collection of views that also have metadata. These tables are listed as system views. All of them are part of the `pg_catalog` schema.


```sql
-- Find indexes in a schema
select 
tablename,
indexname,
indexdef FROM pg_catalog.pg_indexes where schemaname = 'public';
```

```sql
-- Find indexes for a table
select 
tablename,
indexname,
indexdef FROM pg_catalog.pg_indexes where schemaname = 'public' AND tablename='mytable';
```


You can also list materialized views in your database with:
```sql
select 
schemaname,
matviewname,
ispopulated,
definition
FROM pg_matviews where schemaname='public';
```


### [System Catalogs](https://www.postgresql.org/docs/current/catalogs-overview.html)

 "The system catalogs are the place where a relational database management system stores schema metadata, such as information about tables and columns, and internal bookkeeping information."

Like Systems Views, the system catalog tables are also part of the `pg_catalog` schema. This schema, just like the `information_schema` exists by default in your Postgres database.


If I want some estimates about the size of a table, the System Catalog has a table, [pg_class](https://www.postgresql.org/docs/current/catalog-pg-class.html) that lets me inspect the table size and other attributes:

```sql
select relname, relpages, reltuples FROM pg_catalog.pg_class WHERE relname='sales';
```
Output:
```
    relname    | relpages | reltuples 
---------------+----------+-----------
     sales     |        8 |       568

```

Or, with some extra functions, you can calculate the size of your tables and indexes*:

```sql
SELECT relname, pg_relation_size(oid) as bytes, 
          pg_size_pretty(pg_relation_size(oid)) 
     FROM pg_class 
    WHERE relnamespace = 'public'::regnamespace 
    ORDER BY relname;
```
*Query from [Designing high-performance time series data tables on Amazon RDS for PostgreSQL](https://aws.amazon.com/blogs/database/designing-high-performance-time-series-data-tables-on-amazon-rds-for-postgresql/)

```
   relname    |  bytes  | pg_size_pretty 
--------------+---------+----------------
 sales        | 1638400 | 1600 kB
 sales_id_seq |    8192 | 8192 bytes

```

### Putting It All Together
Queries can be really powerful when you join tables across these schemas.
For example, you can list all of the constraints of a table. Here's a query
that will give you all of the constraints for a given table in your database.
```sql
select table_name, column_name, constraint_name, 
case 
	when pgcc.contype = 'p' then 'Primary Key Constraint'
	when pgcc.contype = 'f' then 'Foreign Key Constraint'
	when pgcc.contype = 'c' then 'Check Constraint'
end as constraint_type
, pg_get_constraintdef(pgcc."oid" , true) as constraint_definition 
from information_schema.constraint_column_usage iccu
inner join  pg_catalog.pg_constraint pgcc on iccu.constraint_name = pgcc.conname
where table_name = 'parent';
```
Output:
```sql
 table_name | column_name |       constraint_name        |    constraint_type     |             constraint_definition             
------------+-------------+------------------------------+------------------------+-----------------------------------------------
 parent     | id          | parent_pkey                  | Primary Key Constraint | PRIMARY KEY (id)
 parent     | id          | child_parent_id_fkey         | Foreign Key Constraint | FOREIGN KEY (parent_id) REFERENCES parent(id)
 parent     | parent_name | name_less_than_20_characters | Check Constraint       | CHECK (length(parent_name::text) <= 20)
```

### Wrap Up

 The Postgres Information Schema and Postgres Catalog are great tools to understand your database on a deeper level.

Reference:
[Docs for System Level Metadata](https://www.postgresql.org/docs/current/views.html)